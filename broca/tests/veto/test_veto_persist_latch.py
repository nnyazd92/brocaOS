from __future__ import annotations

import json
from pathlib import Path

from broca.veto.guard import VetoGuard


def _mk_guard(*, state_path: Path, persist_latch: bool) -> VetoGuard:
    # Keep params aligned with get_veto_guard defaults; model weights not needed for this test.
    return VetoGuard(
        enabled=True,
        model_type="gru",
        input_dim=12,
        seq_len=16,
        hidden_dim=32,
        lr=0.001,
        norm_alpha=0.01,
        sigma_mult=1.5,
        fixed_margin=0.0,
        anomaly_mode="residual",
        residual_alpha=0.05,
        residual_k=3.0,
        residual_min_samples=8,
        hysteresis_h=0.05,
        persist_n=8,
        persist_m=5,
        clear_k=3,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
        persist_latch=bool(persist_latch),
        state_path=str(state_path),
        model_path=None,
        save_interval_s=0.0,
    )


def test_veto_latch_not_restored_by_default(tmp_path: Path) -> None:
    p = tmp_path / "veto_state.json"

    # Write a snapshot with an active latch.
    g1 = _mk_guard(state_path=p, persist_latch=True)
    with g1._lock:
        g1._veto_active = True
        g1._clear_count = 2
        g1._violations = [True] * 8
    g1.save_persisted_state(force=True)

    # New guard with persist_latch=False should *not* restore latch state.
    g2 = _mk_guard(state_path=p, persist_latch=False)
    g2.load_persisted_state()
    snap = g2.serialize_state()
    assert snap.get("state", {}).get("veto_active") is False
    assert snap.get("state", {}).get("clear_count") == 0
    assert snap.get("state", {}).get("violations") == []


def test_veto_latch_restored_when_enabled(tmp_path: Path) -> None:
    p = tmp_path / "veto_state.json"

    # Create a persisted snapshot that is latched.
    payload = {
        "version": 1,
        "ts": 0.0,
        "cfg": {"input_dim": 12, "seq_len": 16},
        "state": {"veto_active": True, "clear_count": 1, "violations": [True, True, True, True, True]},
        "buffers": {"xs": []},
        "norm": {"seen": 0, "mean": [0.0] * 12, "var": [0.1] * 12},
        "residual": {"seen": 0, "mean": 0.0, "var": 0.1},
    }
    p.write_text(json.dumps(payload), encoding="utf-8")

    g = _mk_guard(state_path=p, persist_latch=True)
    g.load_persisted_state()
    snap = g.serialize_state()
    assert snap.get("state", {}).get("veto_active") is True
    assert snap.get("state", {}).get("clear_count") == 1
    assert snap.get("state", {}).get("violations") == [True, True, True, True, True]


