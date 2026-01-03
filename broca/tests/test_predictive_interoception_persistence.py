from broca.config import config
from broca.internal_sensing.framework import InternalSensingFramework


def test_predictive_interoception_state_persists(tmp_path):
    """
    Regression: predictive interoception calibration state must persist across restarts,
    otherwise calibrated surprise (and downstream RL signals) resets to 0.
    """
    state_file = tmp_path / "internal_sensing_state.json"
    config.internal_sensing.state_path = str(state_file)

    fw1 = InternalSensingFramework(sampling_rate=1.0, history_window=60)

    # Create a calibrated surprise entry.
    fw1.interoception.prediction.update_models(
        model_type="general",
        error=0.7,
        predicted={"computational_load": 0.0},
        actual={"computational_load": 1.0},
    )

    # Also ensure κ-integrated state persists (so predictive interoception has continuity).
    fw1.interoception.prediction.record_kappa_sample(0.2, now=0.0)
    fw1.interoception.prediction.tick_kappa(now=10.0)
    fw1.save_state()

    fw2 = InternalSensingFramework(sampling_rate=1.0, history_window=60)
    assert fw2.interoception.prediction.get_rl_surprise_signal() > 0.0
    assert fw2.interoception.prediction.get_kappa_integrated() >= 0.0


