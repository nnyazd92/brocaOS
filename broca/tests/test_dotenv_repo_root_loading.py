from __future__ import annotations

import importlib
from pathlib import Path


def test_config_loads_dotenv_from_repo_root_even_if_cwd_is_elsewhere(tmp_path, monkeypatch):
    """
    Regression: config must load `.env` from repo root regardless of current working directory.

    This prevents surprises like Tavily key missing in web_api when the server CWD != repo root.
    """
    # Move away from repo root.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BROCA_TEST_MODE", "false")

    # Patch dotenv.load_dotenv to capture the provided dotenv_path.
    import dotenv

    seen = {}

    def _spy_load_dotenv(*args, **kwargs):
        seen["dotenv_path"] = kwargs.get("dotenv_path")
        seen["override"] = kwargs.get("override")
        return False

    monkeypatch.setattr(dotenv, "load_dotenv", _spy_load_dotenv)

    # Reload broca.config so the top-level load_dotenv call executes with our spy.
    import broca.config as cfg
    import broca

    importlib.reload(cfg)

    expected = str(Path(broca.__file__).resolve().parents[1] / ".env")
    assert seen.get("dotenv_path") == expected
    assert seen.get("override") is True


