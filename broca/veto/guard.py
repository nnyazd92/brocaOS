from __future__ import annotations

import logging
import json
import math
import os
import threading
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def _clamp01(x: float) -> float:
    try:
        v = float(x)
    except Exception:
        return 0.0
    if not math.isfinite(v):
        return 0.0
    return max(0.0, min(1.0, v))


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
    except Exception:
        return float(default)
    if not math.isfinite(v):
        return float(default)
    return float(v)


def _stable_hash01(text: str) -> float:
    # Deterministic across process runs.
    import hashlib

    if not isinstance(text, str):
        text = str(text)
    h = hashlib.sha1(text.encode("utf-8")).digest()
    # Use 4 bytes for a uint32 in [0, 2^32-1]
    u = int.from_bytes(h[:4], "big", signed=False)
    return float(u / 2**32)


@dataclass(frozen=True)
class VetoDecision:
    veto: bool
    reason: str
    threshold: float
    kappa_integrated: float
    kappa_last: float
    debug: Dict[str, Any]


class _EmaNorm:
    """
    Lightweight online normalization for a vector stream.
    Uses EMA mean/var; clamps var to avoid div0.
    """

    def __init__(self, dim: int, *, alpha: float = 0.01) -> None:
        self.dim = int(dim)
        self.alpha = float(alpha)
        self.mean = np.zeros((self.dim,), dtype=np.float64)
        self.var = np.ones((self.dim,), dtype=np.float64) * 0.1
        self._seen = 0

    def update(self, x: np.ndarray) -> None:
        a = float(self.alpha)
        a = max(0.001, min(0.2, a))
        xx = np.asarray(x, dtype=np.float64).reshape(-1)
        if xx.size != self.dim:
            return
        if not np.all(np.isfinite(xx)):
            return
        if self._seen == 0:
            self.mean = xx.copy()
            self.var = np.ones((self.dim,), dtype=np.float64) * 0.1
            self._seen = 1
            return
        delta = xx - self.mean
        self.mean = (1.0 - a) * self.mean + a * xx
        # EMA of squared deviation (variance proxy)
        self.var = (1.0 - a) * self.var + a * (delta * delta)
        self.var = np.clip(self.var, 1e-6, 1e6)
        self._seen += 1

    def normalize(self, x: np.ndarray) -> np.ndarray:
        xx = np.asarray(x, dtype=np.float64).reshape(-1)
        if xx.size != self.dim:
            return np.zeros((self.dim,), dtype=np.float64)
        denom = np.sqrt(np.clip(self.var, 1e-6, 1e6))
        z = (xx - self.mean) / denom
        z = np.where(np.isfinite(z), z, 0.0)
        return z.astype(np.float32, copy=False)


class _TorchSeqModel:
    """
    Tiny GRU/LSTM that predicts next κ_integrated mean + log_sigma given a sequence of slices.
    Used to derive a dynamic threshold scalar for current κ_integrated.
    """

    def __init__(
        self,
        *,
        input_dim: int,
        hidden_dim: int,
        model_type: str,
        lr: float,
        device: str,
    ) -> None:
        import torch
        import torch.nn as nn

        self.torch = torch
        self.nn = nn
        self.device = torch.device(device)
        mt = str(model_type).strip().lower()
        self.model_type = "lstm" if mt == "lstm" else "gru"

        rnn_cls = nn.LSTM if self.model_type == "lstm" else nn.GRU
        self.rnn = rnn_cls(
            input_size=int(input_dim),
            hidden_size=int(hidden_dim),
            num_layers=1,
            batch_first=True,
        ).to(self.device)

        # Heads for heteroscedastic regression of next I.
        self.head_mu = nn.Linear(int(hidden_dim), 1).to(self.device)
        self.head_log_sigma = nn.Linear(int(hidden_dim), 1).to(self.device)

        params = list(self.rnn.parameters()) + list(self.head_mu.parameters()) + list(self.head_log_sigma.parameters())
        self.opt = torch.optim.Adam(params, lr=float(lr))

        self.rnn.train()
        self.head_mu.train()
        self.head_log_sigma.train()

    def forward(self, seq_batch: "Any") -> Tuple["Any", "Any"]:
        torch = self.torch
        # seq_batch: (B, T, D)
        out, _ = self.rnn(seq_batch)
        h_last = out[:, -1, :]
        mu = self.head_mu(h_last).squeeze(-1)
        log_sigma = self.head_log_sigma(h_last).squeeze(-1)
        # Clamp log_sigma for stability.
        log_sigma = torch.clamp(log_sigma, min=-6.0, max=4.0)
        return mu, log_sigma

    def train_step(self, *, seq: np.ndarray, target_i: float) -> Dict[str, float]:
        torch = self.torch
        self.opt.zero_grad(set_to_none=True)
        xb = torch.tensor(seq[None, ...], dtype=torch.float32, device=self.device)  # (1, T, D)
        y = torch.tensor([float(target_i)], dtype=torch.float32, device=self.device)  # (1,)
        mu, log_sigma = self.forward(xb)
        sigma = torch.exp(log_sigma)
        # NLL for Gaussian with learned sigma (heteroscedastic).
        loss = 0.5 * ((y - mu) / (sigma + 1e-6)) ** 2 + log_sigma
        loss = loss.mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(list(self.rnn.parameters()), max_norm=1.0)
        self.opt.step()
        return {"loss": float(loss.detach().cpu().item())}

    def predict(self, *, seq: np.ndarray) -> Tuple[float, float]:
        torch = self.torch
        with torch.no_grad():
            xb = torch.tensor(seq[None, ...], dtype=torch.float32, device=self.device)
            mu, log_sigma = self.forward(xb)
            mu_f = float(mu.detach().cpu().item())
            sigma_f = float(torch.exp(log_sigma).detach().cpu().item())
        if not math.isfinite(mu_f):
            mu_f = 0.0
        if not math.isfinite(sigma_f):
            sigma_f = 0.1
        sigma_f = max(1e-6, min(10.0, sigma_f))
        return mu_f, sigma_f


class VetoGuard:
    """
    Learned Veto guard with persistence/hysteresis.

    This guard is designed to be:
    - lightweight (small model, bounded buffers)
    - best-effort (fail open on internal errors)
    - deterministic-enough in output schema for golden traces
    """

    def __init__(
        self,
        *,
        enabled: bool,
        model_type: str,
        input_dim: int,
        seq_len: int,
        hidden_dim: int,
        lr: float,
        norm_alpha: float,
        sigma_mult: float,
        fixed_margin: float,
        anomaly_mode: str = "threshold",
        residual_alpha: float = 0.05,
        residual_k: float = 3.0,
        residual_min_samples: int = 8,
        hysteresis_h: float,
        persist_n: int,
        persist_m: int,
        clear_k: int,
        max_train_steps_per_obs: int,
        min_train_interval_s: float,
        state_path: Optional[str] = None,
        model_path: Optional[str] = None,
        save_interval_s: float = 1.0,
    ) -> None:
        self.enabled = bool(enabled)
        self.model_type = str(model_type).strip().lower() or "gru"
        self.input_dim = int(input_dim)
        self.seq_len = max(2, int(seq_len))
        self.hidden_dim = max(4, int(hidden_dim))
        self.lr = float(lr)
        self.sigma_mult = float(sigma_mult)
        self.fixed_margin = float(fixed_margin)
        self.anomaly_mode = str(anomaly_mode or "threshold").strip().lower()
        if self.anomaly_mode not in {"threshold", "residual"}:
            self.anomaly_mode = "threshold"
        self.residual_alpha = float(residual_alpha)
        self.residual_k = float(residual_k)
        self.residual_min_samples = max(0, int(residual_min_samples))
        self.hysteresis_h = float(hysteresis_h)
        self.persist_n = max(1, int(persist_n))
        self.persist_m = max(1, min(int(persist_m), int(persist_n)))
        self.clear_k = max(1, int(clear_k))
        self.max_train_steps_per_obs = max(0, int(max_train_steps_per_obs))
        self.min_train_interval_s = max(0.0, float(min_train_interval_s))

        self._lock = threading.Lock()
        self._norm = _EmaNorm(self.input_dim, alpha=float(norm_alpha))

        # ring buffers
        self._xs: list[np.ndarray] = []  # raw slices (float64)
        self._violations: list[bool] = []

        # veto state
        self._veto_active: bool = False
        self._clear_count: int = 0

        # model
        self._torch_model: Optional[_TorchSeqModel] = None
        self._torch_ok: bool = False

        # training throttle
        self._last_train_ts: float = 0.0

        # Residual baseline (EMA mean/var for |I - I_hat|).
        self._res_mean: float = 0.0
        self._res_var: float = 0.1
        self._res_seen: int = 0

        # Persistence (stateful across restarts)
        self._state_path: Optional[str] = (str(state_path).strip() if state_path else None) or None
        self._model_path: Optional[str] = (str(model_path).strip() if model_path else None) or None
        try:
            si = float(save_interval_s)
            if not math.isfinite(si):
                si = 1.0
        except Exception:
            si = 1.0
        self._save_interval_s: float = max(0.0, si)
        self._last_save_ts: float = 0.0

        if self.enabled:
            self._try_init_torch()

    def _atomic_write_json(self, path: str, payload: Dict[str, Any]) -> None:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=str(p.parent),
                delete=False,
                suffix=".tmp",
                encoding="utf-8",
            ) as f:
                json.dump(payload, f, ensure_ascii=False, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
                tmp_name = f.name
            Path(tmp_name).replace(p)
        except Exception:
            # Best-effort: never crash runtime for persistence.
            return

    def serialize_state(self) -> Dict[str, Any]:
        """
        Serialize the *behaviorally relevant* veto state (buffers/EMA/hysteresis),
        so veto decisions remain stateful across restarts.
        """
        try:
            with self._lock:
                xs = [[float(v) for v in x.reshape(-1).tolist()] for x in list(self._xs)]
                mean = [float(v) for v in self._norm.mean.reshape(-1).tolist()]
                var = [float(v) for v in self._norm.var.reshape(-1).tolist()]
                seen = int(getattr(self._norm, "_seen", 0) or 0)
                return {
                    "version": 1,
                    "ts": float(time.time()),
                    "cfg": {
                        "model_type": str(self.model_type),
                        "input_dim": int(self.input_dim),
                        "seq_len": int(self.seq_len),
                        "hidden_dim": int(self.hidden_dim),
                        "anomaly_mode": str(self.anomaly_mode),
                        "persist_n": int(self.persist_n),
                        "persist_m": int(self.persist_m),
                        "clear_k": int(self.clear_k),
                        "hysteresis_h": float(self.hysteresis_h),
                        "sigma_mult": float(self.sigma_mult),
                        "fixed_margin": float(self.fixed_margin),
                        "norm_alpha": float(getattr(self._norm, "alpha", 0.01)),
                        "residual_alpha": float(self.residual_alpha),
                        "residual_k": float(self.residual_k),
                        "residual_min_samples": int(self.residual_min_samples),
                    },
                    "state": {
                        "veto_active": bool(self._veto_active),
                        "clear_count": int(self._clear_count),
                        "violations": [bool(v) for v in list(self._violations)[-int(self.persist_n) :]],
                    },
                    "buffers": {"xs": xs},
                    "norm": {"seen": int(seen), "mean": mean, "var": var},
                    "residual": {"seen": int(self._res_seen), "mean": float(self._res_mean), "var": float(self._res_var)},
                }
        except Exception:
            return {}

    def deserialize_state(self, data: Dict[str, Any]) -> None:
        """
        Restore state from a persisted snapshot (best-effort, backward compatible).
        """
        if not isinstance(data, dict):
            return
        try:
            with self._lock:
                st = data.get("state") or {}
                if isinstance(st, dict):
                    self._veto_active = bool(st.get("veto_active", self._veto_active))
                    try:
                        self._clear_count = int(st.get("clear_count", self._clear_count) or 0)
                    except Exception:
                        pass
                    vio = st.get("violations")
                    if isinstance(vio, list):
                        self._violations = [bool(v) for v in vio][-int(self.persist_n) :]

                buf = data.get("buffers") or {}
                if isinstance(buf, dict):
                    xs = buf.get("xs")
                    if isinstance(xs, list):
                        new_xs: list[np.ndarray] = []
                        for row in xs[-max(self.seq_len * 4, 64) :]:
                            if not isinstance(row, list):
                                continue
                            try:
                                rr = np.asarray([float(v) for v in row], dtype=np.float64).reshape(-1)
                            except Exception:
                                continue
                            if rr.size != int(self.input_dim):
                                continue
                            if not np.all(np.isfinite(rr)):
                                continue
                            new_xs.append(rr)
                        self._xs = new_xs

                norm = data.get("norm") or {}
                if isinstance(norm, dict):
                    mean = norm.get("mean")
                    var = norm.get("var")
                    if isinstance(mean, list) and isinstance(var, list) and len(mean) == int(self.input_dim) and len(var) == int(self.input_dim):
                        mm = np.asarray([float(v) for v in mean], dtype=np.float64).reshape(-1)
                        vv = np.asarray([float(v) for v in var], dtype=np.float64).reshape(-1)
                        if np.all(np.isfinite(mm)) and np.all(np.isfinite(vv)):
                            self._norm.mean = mm
                            self._norm.var = np.clip(vv, 1e-8, 1e6)
                    try:
                        self._norm._seen = int(norm.get("seen", getattr(self._norm, "_seen", 0) or 0) or 0)
                    except Exception:
                        pass

                res = data.get("residual") or {}
                if isinstance(res, dict):
                    try:
                        self._res_seen = int(res.get("seen", self._res_seen) or 0)
                    except Exception:
                        pass
                    try:
                        self._res_mean = float(res.get("mean", self._res_mean))
                    except Exception:
                        pass
                    try:
                        self._res_var = float(res.get("var", self._res_var))
                    except Exception:
                        pass
                    if not math.isfinite(self._res_var):
                        self._res_var = 0.1
                    self._res_var = max(1e-8, min(1e6, float(self._res_var)))
        except Exception:
            return

    def save_persisted_state(self, *, force: bool = False) -> None:
        if not self._state_path:
            return
        if not force:
            try:
                if self._save_interval_s > 0.0 and (time.time() - float(self._last_save_ts)) < float(self._save_interval_s):
                    return
            except Exception:
                pass
        payload = self.serialize_state()
        if not payload:
            return
        self._atomic_write_json(self._state_path, payload)
        self._last_save_ts = float(time.time())

    def load_persisted_state(self) -> None:
        if not self._state_path:
            return
        try:
            p = Path(self._state_path)
            if not p.exists():
                return
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.deserialize_state(data)
        except Exception:
            return

    def _save_model_weights(self) -> None:
        if not self._model_path:
            return
        if not self._torch_ok or self._torch_model is None:
            return
        try:
            import torch  # type: ignore
        except Exception:
            return
        try:
            tm = self._torch_model
            payload = {
                "version": 1,
                "ts": float(time.time()),
                "model_type": str(self.model_type),
                "input_dim": int(self.input_dim),
                "hidden_dim": int(self.hidden_dim),
                "rnn": tm.rnn.state_dict(),
                "head_mu": tm.head_mu.state_dict(),
                "head_log_sigma": tm.head_log_sigma.state_dict(),
            }
            p = Path(self._model_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            torch.save(payload, str(p))
        except Exception:
            return

    def _load_model_weights(self) -> None:
        if not self._model_path:
            return
        if not self._torch_ok or self._torch_model is None:
            return
        try:
            import torch  # type: ignore
        except Exception:
            return
        try:
            p = Path(self._model_path)
            if not p.exists():
                return
            payload = torch.load(str(p), map_location="cpu")
            if not isinstance(payload, dict):
                return
            tm = self._torch_model
            if "rnn" in payload:
                tm.rnn.load_state_dict(payload["rnn"], strict=False)
            if "head_mu" in payload:
                tm.head_mu.load_state_dict(payload["head_mu"], strict=False)
            if "head_log_sigma" in payload:
                tm.head_log_sigma.load_state_dict(payload["head_log_sigma"], strict=False)
        except Exception:
            return
    def _ema_update_scalar(self, *, mean: float, var: float, x: float, alpha: float) -> Tuple[float, float]:
        a = float(alpha)
        a = max(0.001, min(0.5, a))
        m = float(mean)
        v = float(var)
        dx = float(x) - m
        m2 = (1.0 - a) * m + a * float(x)
        v2 = (1.0 - a) * v + a * (dx * dx)
        if not math.isfinite(v2):
            v2 = 0.1
        v2 = max(1e-8, min(1e6, v2))
        return float(m2), float(v2)

    def _predict_next_i_from_prev(self) -> Tuple[Optional[float], Optional[float], Dict[str, Any]]:
        """
        Predict current I from the previous seq_len slices (residual mode).
        Returns (mu, sigma, debug). mu/sigma None when unavailable/warmup.
        """
        if not self._torch_ok or self._torch_model is None:
            return None, None, {"ok": False, "reason": "torch_unavailable"}
        if len(self._xs) < (self.seq_len + 1):
            return None, None, {"ok": False, "reason": "warmup"}
        # Use the previous seq_len slices to predict the current slice's I.
        prev = self._xs[-(self.seq_len + 1) : -1]
        seq = self._seq_norm(prev)
        try:
            mu, sigma = self._torch_model.predict(seq=seq)
            return float(mu), float(sigma), {"ok": True, "mu": float(mu), "sigma": float(sigma)}
        except Exception as e:
            return None, None, {"ok": False, "reason": f"pred_error:{type(e).__name__}"}

    def _try_init_torch(self) -> None:
        try:
            import torch  # noqa: F401

            device = os.getenv("BROCA_VETO_DEVICE", "cpu")
            self._torch_model = _TorchSeqModel(
                input_dim=int(self.input_dim),
                hidden_dim=int(self.hidden_dim),
                model_type=str(self.model_type),
                lr=float(self.lr),
                device=str(device),
            )
            self._torch_ok = True
        except Exception as e:
            self._torch_ok = False
            self._torch_model = None
            logger.warning(f"VetoGuard torch backend unavailable; disabling learned veto: {e}")
            self.enabled = False

    @staticmethod
    def build_time_slice(
        *,
        kappa_last: float,
        kappa_integrated: float,
        rl_signals: Optional[Dict[str, Any]] = None,
        tool_name: str = "",
        tool_success_last: Optional[bool] = None,
        tool_count_this_turn: Optional[int] = None,
    ) -> np.ndarray:
        rl = rl_signals if isinstance(rl_signals, dict) else {}

        # Prefer varnorm keys when present; fall back to raw.
        def s(key: str, default: float) -> float:
            return _clamp01(_safe_float(rl.get(f"{key}_varnorm", rl.get(key, default)), default))

        # Normalize κ to [0,1]; κ_integrated is in time-units (can exceed 1.0).
        k_last = _clamp01(kappa_last)
        k_int = max(0.0, _safe_float(kappa_integrated, 0.0))

        # Tool context features (bounded)
        tool_id = _stable_hash01(str(tool_name or ""))
        succ = 0.5
        if tool_success_last is not None:
            succ = 1.0 if bool(tool_success_last) else 0.0
        tc = 0.0
        if tool_count_this_turn is not None:
            tc = max(0.0, min(1.0, float(int(tool_count_this_turn)) / 10.0))

        # RL signals are already shaped to [0,1] in many parts of the system.
        x = np.array(
            [
                k_last,
                k_int,
                s("composite_reward", 0.5),
                s("coherence_reward", 0.5),
                s("dissonance_reward", 0.5),
                s("surprise_reward", 0.5),
                s("curiosity_reward", 0.5),
                s("information_gain_reward", 0.5),
                tool_id,
                succ,
                tc,
                # A small bias term for stability.
                1.0,
            ],
            dtype=np.float64,
        )
        return x

    def _append_slice(self, x: np.ndarray) -> None:
        self._xs.append(x)
        # Cap raw buffer to avoid unbounded growth.
        max_keep = max(self.seq_len * 4, 64)
        if len(self._xs) > max_keep:
            self._xs = self._xs[-max_keep:]

    def _seq_norm(self, xs: list[np.ndarray]) -> np.ndarray:
        # xs list of raw slices (float64), returns (T,D) float32 normalized.
        arr = np.stack(xs, axis=0).astype(np.float64, copy=False)
        # Update normalization on the newest sample only (to reduce feedback coupling).
        try:
            self._norm.update(arr[-1])
        except Exception:
            pass
        out = np.stack([self._norm.normalize(v) for v in arr], axis=0)
        return out.astype(np.float32, copy=False)

    def _train_if_ready(self) -> Dict[str, Any]:
        """
        Self-supervised: use the previous seq_len slices to predict the next slice's κ_integrated.
        """
        if not self._torch_ok or self._torch_model is None:
            return {"trained": False, "reason": "torch_unavailable"}
        if self.max_train_steps_per_obs <= 0:
            return {"trained": False, "reason": "train_disabled"}
        if len(self._xs) < (self.seq_len + 1):
            return {"trained": False, "reason": "warmup"}
        now = time.time()
        if self.min_train_interval_s > 0.0 and (now - self._last_train_ts) < self.min_train_interval_s:
            return {"trained": False, "reason": "throttled"}

        prev = self._xs[-(self.seq_len + 1) : -1]
        cur = self._xs[-1]
        target_i = float(cur[1])  # κ_integrated lives at index 1 in our slice schema.
        seq = self._seq_norm(prev)
        out: Dict[str, Any] = {"trained": False}
        try:
            for _ in range(int(self.max_train_steps_per_obs)):
                metrics = self._torch_model.train_step(seq=seq, target_i=target_i)
                out = {"trained": True, **metrics}
        except Exception as e:
            return {"trained": False, "reason": f"train_error:{type(e).__name__}"}
        self._last_train_ts = now
        return out

    def _predict_threshold(self) -> Tuple[float, Dict[str, Any]]:
        """
        Predict dynamic threshold for κ_integrated (I).
        Returns (threshold, debug).
        """
        if not self._torch_ok or self._torch_model is None:
            return 0.0, {"ok": False, "reason": "torch_unavailable"}
        if len(self._xs) < self.seq_len:
            return 0.0, {"ok": False, "reason": "warmup"}
        seq_raw = self._xs[-self.seq_len :]
        seq = self._seq_norm(seq_raw)
        mu, sigma = self._torch_model.predict(seq=seq)

        # Convert predicted next-I into a conservative threshold for current-I.
        # If sigma is large, threshold increases (more conservative).
        margin = float(self.fixed_margin) + float(self.sigma_mult) * float(sigma)
        thr = float(mu) - float(margin)
        if not math.isfinite(thr):
            thr = 0.0
        thr = max(0.0, thr)
        return thr, {"ok": True, "mu": float(mu), "sigma": float(sigma), "margin": float(margin)}

    def check(
        self,
        *,
        x_t: np.ndarray,
        reason: str,
        kappa_last: float,
        kappa_integrated: float,
    ) -> VetoDecision:
        """
        Observe current slice, compute threshold, and update veto state machine.
        Fail-open: if disabled or errors occur, returns veto=False.
        """
        if not self.enabled:
            return VetoDecision(
                veto=False,
                reason="disabled",
                threshold=0.0,
                kappa_integrated=float(kappa_integrated),
                kappa_last=float(kappa_last),
                debug={"enabled": False},
            )

        should_save = False
        should_save_weights = False
        decision: Optional[VetoDecision] = None

        with self._lock:
            # Append slice and train (best-effort).
            try:
                self._append_slice(np.asarray(x_t, dtype=np.float64).reshape(-1))
            except Exception:
                pass
            train_dbg = self._train_if_ready()

            I = max(0.0, _safe_float(kappa_integrated, 0.0))
            thr = 0.0
            pred_dbg: Dict[str, Any] = {}
            residual_dbg: Dict[str, Any] = {}

            if self.anomaly_mode == "residual":
                mu, sigma, pred_dbg = self._predict_next_i_from_prev()
                if mu is None:
                    # No prediction yet -> no violation (fail-open) while warming up.
                    violation = False
                    thr = 0.0
                    residual_dbg = {
                        "mode": "residual",
                        "ok": False,
                        "reason": str(pred_dbg.get("reason") or "warmup"),
                        "res_mean": float(self._res_mean),
                        "res_var": float(self._res_var),
                        "res_seen": int(self._res_seen),
                    }
                else:
                    err = abs(float(I) - float(mu))
                    if not math.isfinite(err):
                        err = 0.0

                    # Compute threshold from current baseline.
                    res_std = math.sqrt(max(1e-8, float(self._res_var)))
                    err_thr = float(self._res_mean) + float(self.residual_k) * float(res_std)
                    if not math.isfinite(err_thr):
                        err_thr = 0.0
                    err_thr = max(0.0, err_thr)

                    # Warmup gating: require some baseline samples before flagging.
                    enough = int(self._res_seen) >= int(self.residual_min_samples)
                    if not enough:
                        violation = False
                    else:
                        violation = bool(err > float(err_thr))
                    thr = float(err_thr)

                    # Update baseline:
                    # - always during warmup
                    # - after warmup only on non-violation AND when not currently vetoing
                    if not enough:
                        self._res_mean, self._res_var = self._ema_update_scalar(
                            mean=float(self._res_mean),
                            var=float(self._res_var),
                            x=float(err),
                            alpha=float(self.residual_alpha),
                        )
                        self._res_seen += 1
                    elif (not self._veto_active) and (not violation):
                        self._res_mean, self._res_var = self._ema_update_scalar(
                            mean=float(self._res_mean),
                            var=float(self._res_var),
                            x=float(err),
                            alpha=float(self.residual_alpha),
                        )
                        self._res_seen += 1

                    residual_dbg = {
                        "mode": "residual",
                        "ok": True,
                        "err": float(err),
                        "err_thr": float(err_thr),
                        "res_mean": float(self._res_mean),
                        "res_var": float(self._res_var),
                        "res_seen": int(self._res_seen),
                        "enough_samples": bool(enough),
                    }
            else:
                thr, pred_dbg = self._predict_threshold()
                violation = bool(I < float(thr))
                residual_dbg = {"mode": "threshold"}

            # Persistence/hysteresis state machine.
            prev_active = bool(self._veto_active)
            if not self._veto_active:
                self._violations.append(bool(violation))
                if len(self._violations) > self.persist_n:
                    self._violations = self._violations[-self.persist_n :]
                count = int(sum(1 for v in self._violations if v))
                if count >= self.persist_m:
                    self._veto_active = True
                    self._clear_count = 0
            else:
                # Clear rule depends on anomaly mode:
                # - threshold mode: clear when I is safely above threshold + hysteresis
                # - residual mode: clear when the violation condition is False for clear_k consecutive steps
                if self.anomaly_mode == "residual":
                    if not bool(violation):
                        self._clear_count += 1
                    else:
                        self._clear_count = 0
                else:
                    if I > (float(thr) + float(self.hysteresis_h)):
                        self._clear_count += 1
                    else:
                        self._clear_count = 0
                if self._clear_count >= self.clear_k:
                    self._veto_active = False
                    self._clear_count = 0
                    self._violations = []

            state_changed = bool(prev_active != bool(self._veto_active))
            try:
                trained = bool(train_dbg.get("trained", False)) if isinstance(train_dbg, dict) else False
            except Exception:
                trained = False
            should_save = bool(state_changed or trained)
            should_save_weights = bool(trained)
            debug = {
                "enabled": True,
                "reason": str(reason),
                "threshold_mode": str(self.anomaly_mode),
                "threshold": float(thr),
                "violation": bool(violation),
                "state_changed": bool(state_changed),
                "persist_n": int(self.persist_n),
                "persist_m": int(self.persist_m),
                "violations_window": list(self._violations[-self.persist_n :]),
                "veto_active": bool(self._veto_active),
                "clear_k": int(self.clear_k),
                "clear_count": int(self._clear_count),
                "hysteresis_h": float(self.hysteresis_h),
                "pred": pred_dbg,
                "residual": residual_dbg,
                "train": train_dbg,
            }

            decision = VetoDecision(
                veto=bool(self._veto_active),
                reason=str(reason),
                threshold=float(thr),
                kappa_integrated=float(I),
                kappa_last=float(_clamp01(kappa_last)),
                debug=debug,
            )

        # Persist outside the lock to avoid blocking the decision loop.
        if should_save:
            try:
                self.save_persisted_state()
            except Exception:
                pass
        if should_save_weights:
            try:
                self._save_model_weights()
            except Exception:
                pass

        return decision or VetoDecision(
            veto=False,
            reason="error",
            threshold=0.0,
            kappa_integrated=float(kappa_integrated),
            kappa_last=float(kappa_last),
            debug={"enabled": bool(self.enabled), "reason": "decision_missing"},
        )


_global_guard: Optional[VetoGuard] = None
_global_sig: Optional[Tuple[Any, ...]] = None


def get_veto_guard() -> VetoGuard:
    """
    Singleton guard with env/config-driven reconfiguration.

    Reconfigures when the signature changes, similar to other loggers in the repo.
    """
    global _global_guard
    global _global_sig

    # Lazy import to avoid importing config during module import in some edge cases.
    try:
        from broca.config import config

        cfg = getattr(config, "veto", None)
    except Exception:
        cfg = None

    enabled = bool(getattr(cfg, "enabled", os.getenv("BROCA_VETO_ENABLED", "true").lower() == "true"))
    model_type = str(getattr(cfg, "model_type", os.getenv("BROCA_VETO_MODEL_TYPE", "gru")))
    seq_len = int(getattr(cfg, "seq_len", int(os.getenv("BROCA_VETO_SEQ_LEN", "16"))))
    hidden_dim = int(getattr(cfg, "hidden_dim", int(os.getenv("BROCA_VETO_HIDDEN_DIM", "32"))))
    lr = float(getattr(cfg, "learning_rate", float(os.getenv("BROCA_VETO_LR", "0.001"))))
    norm_alpha = float(getattr(cfg, "norm_alpha", float(os.getenv("BROCA_VETO_NORM_ALPHA", "0.01"))))
    sigma_mult = float(getattr(cfg, "sigma_multiplier", float(os.getenv("BROCA_VETO_SIGMA_MULT", "1.5"))))
    fixed_margin = float(getattr(cfg, "fixed_margin", float(os.getenv("BROCA_VETO_FIXED_MARGIN", "0.0"))))
    anomaly_mode = str(getattr(cfg, "anomaly_mode", os.getenv("BROCA_VETO_ANOMALY_MODE", "threshold"))).strip().lower()
    residual_alpha = float(getattr(cfg, "residual_alpha", float(os.getenv("BROCA_VETO_RESIDUAL_ALPHA", "0.05"))))
    residual_k = float(getattr(cfg, "residual_k", float(os.getenv("BROCA_VETO_RESIDUAL_K", "3.0"))))
    residual_min_samples = int(getattr(cfg, "residual_min_samples", int(os.getenv("BROCA_VETO_RESIDUAL_MIN_SAMPLES", "8"))))
    hysteresis_h = float(getattr(cfg, "hysteresis_h", float(os.getenv("BROCA_VETO_HYSTERESIS_H", "0.05"))))
    persist_n = int(getattr(cfg, "persistence_n", int(os.getenv("BROCA_VETO_PERSIST_N", "8"))))
    persist_m = int(getattr(cfg, "persistence_m", int(os.getenv("BROCA_VETO_PERSIST_M", "5"))))
    clear_k = int(getattr(cfg, "clear_k", int(os.getenv("BROCA_VETO_CLEAR_K", "3"))))
    max_train_steps = int(getattr(cfg, "max_train_steps_per_observation", int(os.getenv("BROCA_VETO_MAX_TRAIN_STEPS", "1"))))
    min_train_interval_s = float(getattr(cfg, "min_train_interval_s", float(os.getenv("BROCA_VETO_MIN_TRAIN_INTERVAL_S", "0.2"))))
    state_path = str(getattr(cfg, "state_path", os.getenv("BROCA_VETO_STATE_PATH", "runtime/veto_guard_state.json")) or "").strip()
    model_path = str(getattr(cfg, "model_path", os.getenv("BROCA_VETO_MODEL_PATH", "models/rl/veto_guard.pt")) or "").strip()
    save_interval_s = float(getattr(cfg, "save_interval_s", float(os.getenv("BROCA_VETO_SAVE_INTERVAL_S", "1.0"))))

    # Keep input_dim fixed by the slice schema length.
    input_dim = 12

    # Resolve persistence paths to absolute paths (avoid CWD-dependent resets).
    try:
        repo_root = Path(__file__).resolve().parents[2]
        if state_path and not Path(state_path).is_absolute():
            state_path = str((repo_root / state_path).resolve())
        if model_path and not Path(model_path).is_absolute():
            model_path = str((repo_root / model_path).resolve())
    except Exception:
        pass

    sig = (
        enabled,
        model_type,
        input_dim,
        seq_len,
        hidden_dim,
        lr,
        norm_alpha,
        sigma_mult,
        fixed_margin,
        anomaly_mode,
        residual_alpha,
        residual_k,
        residual_min_samples,
        hysteresis_h,
        persist_n,
        persist_m,
        clear_k,
        max_train_steps,
        min_train_interval_s,
        state_path,
        model_path,
        save_interval_s,
    )

    if _global_guard is None or _global_sig != sig:
        _global_guard = VetoGuard(
            enabled=enabled,
            model_type=model_type,
            input_dim=int(input_dim),
            seq_len=int(seq_len),
            hidden_dim=int(hidden_dim),
            lr=float(lr),
            norm_alpha=float(norm_alpha),
            sigma_mult=float(sigma_mult),
            fixed_margin=float(fixed_margin),
            anomaly_mode=str(anomaly_mode),
            residual_alpha=float(residual_alpha),
            residual_k=float(residual_k),
            residual_min_samples=int(residual_min_samples),
            hysteresis_h=float(hysteresis_h),
            persist_n=int(persist_n),
            persist_m=int(persist_m),
            clear_k=int(clear_k),
            max_train_steps_per_obs=int(max_train_steps),
            min_train_interval_s=float(min_train_interval_s),
            state_path=state_path if state_path else None,
            model_path=model_path if model_path else None,
            save_interval_s=float(save_interval_s),
        )
        # Load persisted state/weights best-effort.
        try:
            _global_guard.load_persisted_state()
        except Exception:
            pass
        try:
            _global_guard._load_model_weights()
        except Exception:
            pass
        _global_sig = sig
    return _global_guard


