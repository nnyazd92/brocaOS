from __future__ import annotations

import builtins
import os
from pathlib import Path
from typing import Any, Callable, Optional


def _is_write_mode(mode: str) -> bool:
    m = (mode or "").lower()
    return any(ch in m for ch in ("w", "a", "x", "+"))


def install_repo_write_guard(
    *,
    repo_root: Optional[str | os.PathLike[str]] = None,
    allow_repo_subpaths: Optional[list[str]] = None,
) -> Callable[[], None]:
    """
    Install a guard that prevents *tests* from writing/appending to repo paths like `data/` or `models/`.

    This is intentionally conservative: it blocks writes under repo_root except for allowed subpaths
    (e.g., `broca/tests/fixtures` for golden traces).

    Returns an uninstall callback.
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    root = root.resolve()
    allow = [Path(p) for p in (allow_repo_subpaths or [])]
    allow_resolved = []
    for p in allow:
        try:
            allow_resolved.append((root / p).resolve() if not p.is_absolute() else p.resolve())
        except Exception:
            continue

    orig_open = builtins.open
    orig_path_open = Path.open

    def _is_allowed(path: Path) -> bool:
        try:
            rp = path.resolve()
        except Exception:
            return True  # fail open for weird paths
        # Allow anything outside repo.
        try:
            rp.relative_to(root)
        except Exception:
            return True
        # Allow explicitly permitted subpaths.
        for a in allow_resolved:
            try:
                rp.relative_to(a)
                return True
            except Exception:
                continue
        # Otherwise disallow writes under repo.
        return False

    def guarded_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any):
        if _is_write_mode(mode):
            try:
                p = Path(file)
                if not _is_allowed(p):
                    raise RuntimeError(
                        f"TEST_WRITE_GUARD: refusing to write to repo path: {str(p)} "
                        f"(set BROCA_TEST_ALLOW_WORKSPACE_RL_WRITES=true to disable sandboxing)"
                    )
            except TypeError:
                # Non-path-like, ignore.
                pass
        return orig_open(file, mode, *args, **kwargs)

    def guarded_path_open(self: Path, mode: str = "r", *args: Any, **kwargs: Any):
        if _is_write_mode(mode):
            if not _is_allowed(self):
                raise RuntimeError(
                    f"TEST_WRITE_GUARD: refusing to write to repo path: {str(self)} "
                    f"(set BROCA_TEST_ALLOW_WORKSPACE_RL_WRITES=true to disable sandboxing)"
                )
        return orig_path_open(self, mode, *args, **kwargs)

    builtins.open = guarded_open  # type: ignore[assignment]
    Path.open = guarded_path_open  # type: ignore[assignment]

    def uninstall() -> None:
        builtins.open = orig_open  # type: ignore[assignment]
        Path.open = orig_path_open  # type: ignore[assignment]

    return uninstall


