from __future__ import annotations

import json
from pathlib import Path

import pytest

from broca.rl.policy_versions import PolicyVersionStore


def test_policy_version_store_atomic_copy_fault_injection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Fault injection: simulate os.replace failure during artifact copy.

    Expectation: active files remain unchanged (and no partial overwrite occurs).
    """
    active_model = tmp_path / "active_model.pt"
    active_buffer = tmp_path / "active_buffer.json"
    active_model.write_bytes(b"ACTIVE")
    active_buffer.write_text(json.dumps({"active": True}), encoding="utf-8")

    store = PolicyVersionStore(store_path=str(tmp_path / "versions.json"), archive_dir=str(tmp_path / "archive"))

    def _boom(*args, **kwargs):
        raise OSError("injected replace failure")

    monkeypatch.setattr("broca.rl.policy_versions.os.replace", _boom)

    with pytest.raises(OSError):
        store.create_version(
            algorithm="online_nn",
            active_model_path=str(active_model),
            active_buffer_path=str(active_buffer),
            status="candidate",
            label="v1",
        )

    assert active_model.read_bytes() == b"ACTIVE"
    assert json.loads(active_buffer.read_text(encoding="utf-8")) == {"active": True}

