from __future__ import annotations

import json
from pathlib import Path

from broca.config import config
from broca.rl.policy_active import apply_active_policy_version
from broca.rl.policy_versions import PolicyVersionStore


def test_apply_active_policy_version_restores_active_paths(tmp_path: Path):
    original = {
        "algorithm": config.rl.algorithm,
        "model_path": config.rl.model_path,
        "buffer_path": config.rl.buffer_path,
        "policy_versions_path": config.rl.policy_versions_path,
        "policy_archive_dir": config.rl.policy_archive_dir,
    }
    try:
        config.rl.algorithm = "online_nn"
        config.rl.model_path = str(tmp_path / "active_model.pt")
        config.rl.buffer_path = str(tmp_path / "active_buffer.json")
        config.rl.policy_versions_path = str(tmp_path / "policy_versions.json")
        config.rl.policy_archive_dir = str(tmp_path / "policy_versions")

        # Create active artifacts and snapshot as v1.
        Path(config.rl.model_path).parent.mkdir(parents=True, exist_ok=True)
        Path(config.rl.buffer_path).parent.mkdir(parents=True, exist_ok=True)
        Path(config.rl.model_path).write_bytes(b"MODEL_V1")
        Path(config.rl.buffer_path).write_text(json.dumps([{"tool_name": "A"}]), encoding="utf-8")

        store = PolicyVersionStore(store_path=str(config.rl.policy_versions_path), archive_dir=str(config.rl.policy_archive_dir))
        entry = store.create_version(
            algorithm="online_nn",
            active_model_path=str(config.rl.model_path),
            active_buffer_path=str(config.rl.buffer_path),
            status="candidate",
            label="v1",
        )
        ok, _ = store.set_active(int(entry["version_id"]))
        assert ok is True

        # Corrupt active paths, then apply active version.
        Path(config.rl.model_path).write_bytes(b"CORRUPT")
        Path(config.rl.buffer_path).write_text("[]", encoding="utf-8")

        applied, info = apply_active_policy_version(runtime_algorithm="online_nn")
        assert applied is True
        assert int(info.get("version_id")) == 1
        assert Path(config.rl.model_path).read_bytes() == b"MODEL_V1"
    finally:
        config.rl.algorithm = original["algorithm"]
        config.rl.model_path = original["model_path"]
        config.rl.buffer_path = original["buffer_path"]
        config.rl.policy_versions_path = original["policy_versions_path"]
        config.rl.policy_archive_dir = original["policy_archive_dir"]

