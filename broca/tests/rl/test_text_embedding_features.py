import numpy as np
from hypothesis import given, strategies as st

from broca.rl.text_embedding import hash_text_embedding
from broca.rl.features import extract_state_features, BASE_STATE_DIM


def test_hash_text_embedding_deterministic():
    v1 = hash_text_embedding("Hello world", 8)
    v2 = hash_text_embedding("Hello world", 8)
    assert np.allclose(v1, v2)


@given(st.text(min_size=0, max_size=200))
def test_hash_text_embedding_shape_and_finite(s):
    v = hash_text_embedding(s, 16)
    assert v.shape == (16,)
    assert np.isfinite(v).all()


def test_extract_state_features_appends_text_embedding():
    ctx = {
        "rl_signals": {
            "dissonance_reward": 0.1,
            "surprise_reward": 0.2,
            "curiosity_reward": 0.3,
            "information_gain_reward": 0.4,
            "coherence_reward": 0.5,
            "exploration_balance": 0.6,
        },
        "text_features": {"user_prompt": "please use terminal", "last_assistant": "ok"},
    }
    x = extract_state_features(ctx, input_dim=BASE_STATE_DIM + 12, text_embedding_dim=12, text_fields=["user_prompt", "last_assistant"])
    assert x.shape == (BASE_STATE_DIM + 12,)
    # At least one appended component should be non-zero for non-empty text.
    assert float(np.abs(x[BASE_STATE_DIM:]).sum()) > 0.0

