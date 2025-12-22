import os
import tempfile
from pathlib import Path
import sys
# Ensure project root is on sys.path so tests can import broca package when
# run from the repository root.
sys.path.insert(0, os.path.abspath(os.getcwd()))

from broca.world_state.directory_structure import DirectoryStructureGenerator


def make_tree(root: Path, structure: dict):
    for name, value in structure.items():
        if value is None:
            (root / name).write_text("content")
        else:
            (root / name).mkdir(parents=True, exist_ok=True)
            make_tree(root / name, value)


def test_skip_hidden_and_pycache(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    # create visible file and hidden file and __pycache__ dir
    make_tree(root, {"visible.txt": None, ".hidden": None, "__pycache__": {"a.pyc": None}})

    gen = DirectoryStructureGenerator(str(root))
    files, dirs = gen.scan_directory()

    paths = [f["path"] for f in files]
    assert "visible.txt" in [Path(p).name for p in paths]
    assert ".hidden" not in [Path(p).name for p in paths]
    assert "__pycache__" not in dirs


def test_include_hidden_flag(tmp_path: Path):
    root = tmp_path / "repo2"
    root.mkdir()
    make_tree(root, {"visible.txt": None, ".hidden": None})

    gen = DirectoryStructureGenerator(str(root))
    gen.include_hidden = True
    files, dirs = gen.scan_directory()
    assert ".hidden" in [Path(p)[-1] if isinstance(Path(p), list) else Path(p)[-1] for p in [f["path"] for f in files]]

