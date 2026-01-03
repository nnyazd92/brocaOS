import numpy as np


def test_veto_guard_persistence_roundtrip_state_only(tmp_path):
    """
    Persistence should round-trip *behavioral state* even if torch/model is unavailable.
    This keeps veto hysteresis and residual baseline stateful across restarts.
    """
    from broca.veto.guard import VetoGuard

    state_path = tmp_path / "veto_guard_state.json"

    g1 = VetoGuard(
        enabled=False,  # avoid torch dependency in this unit test
        model_type="gru",
        input_dim=12,
        seq_len=8,
        hidden_dim=16,
        lr=1e-3,
        norm_alpha=0.01,
        sigma_mult=1.5,
        fixed_margin=0.0,
        anomaly_mode="residual",
        residual_alpha=0.05,
        residual_k=3.0,
        residual_min_samples=2,
        hysteresis_h=0.05,
        persist_n=5,
        persist_m=3,
        clear_k=2,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
        state_path=str(state_path),
        model_path=None,
        save_interval_s=0.0,
    )

    # Seed non-default internal state
    with g1._lock:
        g1._veto_active = True
        g1._clear_count = 1
        g1._violations = [True, True, False, True]
        g1._xs = [
            np.asarray([0.1] * 12, dtype=np.float64),
            np.asarray([0.2] * 12, dtype=np.float64),
        ]
        g1._norm.mean = np.asarray([0.3] * 12, dtype=np.float64)
        g1._norm.var = np.asarray([0.4] * 12, dtype=np.float64)
        g1._norm._seen = 7  # pylint: disable=protected-access
        g1._res_mean = 0.12
        g1._res_var = 0.34
        g1._res_seen = 9

    g1.save_persisted_state(force=True)
    assert state_path.exists()

    g2 = VetoGuard(
        enabled=False,
        model_type="gru",
        input_dim=12,
        seq_len=8,
        hidden_dim=16,
        lr=1e-3,
        norm_alpha=0.01,
        sigma_mult=1.5,
        fixed_margin=0.0,
        anomaly_mode="residual",
        residual_alpha=0.05,
        residual_k=3.0,
        residual_min_samples=2,
        hysteresis_h=0.05,
        persist_n=5,
        persist_m=3,
        clear_k=2,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
        state_path=str(state_path),
        model_path=None,
        save_interval_s=0.0,
    )
    g2.load_persisted_state()

    with g2._lock:
        assert g2._veto_active is True
        assert g2._clear_count == 1
        assert g2._violations == [True, True, False, True]
        assert len(g2._xs) == 2
        assert float(g2._xs[0][0]) == 0.1
        assert float(g2._xs[1][0]) == 0.2
        assert g2._norm._seen == 7  # pylint: disable=protected-access
        assert float(g2._norm.mean[0]) == 0.3
        assert float(g2._norm.var[0]) == 0.4
        assert g2._res_seen == 9
        assert abs(float(g2._res_mean) - 0.12) < 1e-9
        assert abs(float(g2._res_var) - 0.34) < 1e-9


def test_veto_guard_persistence_saves_weights_when_torch_available(tmp_path):
    """
    If torch is available, we should be able to save/load the GRU/LSTM weights.
    Skip gracefully if torch isn't installed in the test environment.
    """
    try:
        import torch  # noqa: F401
    except Exception:
        return

    from broca.veto.guard import VetoGuard

    state_path = tmp_path / "veto_guard_state.json"
    model_path = tmp_path / "veto_guard.pt"

    g1 = VetoGuard(
        enabled=True,
        model_type="gru",
        input_dim=12,
        seq_len=4,
        hidden_dim=8,
        lr=1e-3,
        norm_alpha=0.01,
        sigma_mult=1.5,
        fixed_margin=0.0,
        anomaly_mode="threshold",
        residual_alpha=0.05,
        residual_k=3.0,
        residual_min_samples=2,
        hysteresis_h=0.05,
        persist_n=3,
        persist_m=2,
        clear_k=2,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
        state_path=str(state_path),
        model_path=str(model_path),
        save_interval_s=0.0,
    )

    # If torch init failed, don't assert on weights file.
    if not getattr(g1, "_torch_ok", False):
        return

    g1._save_model_weights()
    assert model_path.exists()

    g2 = VetoGuard(
        enabled=True,
        model_type="gru",
        input_dim=12,
        seq_len=4,
        hidden_dim=8,
        lr=1e-3,
        norm_alpha=0.01,
        sigma_mult=1.5,
        fixed_margin=0.0,
        anomaly_mode="threshold",
        residual_alpha=0.05,
        residual_k=3.0,
        residual_min_samples=2,
        hysteresis_h=0.05,
        persist_n=3,
        persist_m=2,
        clear_k=2,
        max_train_steps_per_obs=0,
        min_train_interval_s=0.0,
        state_path=str(state_path),
        model_path=str(model_path),
        save_interval_s=0.0,
    )
    if not getattr(g2, "_torch_ok", False):
        return
    g2._load_model_weights()


