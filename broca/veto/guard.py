from __future__ import annotations

import logging
import math
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

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
        hysteresis_h: float,
        persist_n: int,
        persist_m: int,
        clear_k: int,
        max_train_steps_per_obs: int,
        min_train_interval_s: float,
    ) -> None:
        self.enabled = bool(enabled)
        self.model_type = str(model_type).strip().lower() or "gru"
        self.input_dim = int(input_dim)
        self.seq_len = max(2, int(seq_len))
        self.hidden_dim = max(4, int(hidden_dim))
        self.lr = float(lr)
        self.sigma_mult = float(sigma_mult)
        self.fixed_margin = float(fixed_margin)
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

        if self.enabled:
            self._try_init_torch()

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

        with self._lock:
            # Append slice and train (best-effort).
            try:
                self._append_slice(np.asarray(x_t, dtype=np.float64).reshape(-1))
            except Exception:
                pass
            train_dbg = self._train_if_ready()

            thr, pred_dbg = self._predict_threshold()

            I = max(0.0, _safe_float(kappa_integrated, 0.0))
            violation = bool(I < float(thr))

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
                # Clear only when I is safely above threshold + hysteresis for clear_k consecutive steps.
                if I > (float(thr) + float(self.hysteresis_h)):
                    self._clear_count += 1
                else:
                    self._clear_count = 0
                if self._clear_count >= self.clear_k:
                    self._veto_active = False
                    self._clear_count = 0
                    self._violations = []

            state_changed = bool(prev_active != bool(self._veto_active))
            debug = {
                "enabled": True,
                "reason": str(reason),
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
                "train": train_dbg,
            }

            return VetoDecision(
                veto=bool(self._veto_active),
                reason=str(reason),
                threshold=float(thr),
                kappa_integrated=float(I),
                kappa_last=float(_clamp01(kappa_last)),
                debug=debug,
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
    hysteresis_h = float(getattr(cfg, "hysteresis_h", float(os.getenv("BROCA_VETO_HYSTERESIS_H", "0.05"))))
    persist_n = int(getattr(cfg, "persistence_n", int(os.getenv("BROCA_VETO_PERSIST_N", "8"))))
    persist_m = int(getattr(cfg, "persistence_m", int(os.getenv("BROCA_VETO_PERSIST_M", "5"))))
    clear_k = int(getattr(cfg, "clear_k", int(os.getenv("BROCA_VETO_CLEAR_K", "3"))))
    max_train_steps = int(getattr(cfg, "max_train_steps_per_observation", int(os.getenv("BROCA_VETO_MAX_TRAIN_STEPS", "1"))))
    min_train_interval_s = float(getattr(cfg, "min_train_interval_s", float(os.getenv("BROCA_VETO_MIN_TRAIN_INTERVAL_S", "0.2"))))

    # Keep input_dim fixed by the slice schema length.
    input_dim = 12

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
        hysteresis_h,
        persist_n,
        persist_m,
        clear_k,
        max_train_steps,
        min_train_interval_s,
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
            hysteresis_h=float(hysteresis_h),
            persist_n=int(persist_n),
            persist_m=int(persist_m),
            clear_k=int(clear_k),
            max_train_steps_per_obs=int(max_train_steps),
            min_train_interval_s=float(min_train_interval_s),
        )
        _global_sig = sig
    return _global_guard


