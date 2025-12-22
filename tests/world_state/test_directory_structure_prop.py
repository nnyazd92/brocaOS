from hypothesis import given, strategies as st
from pathlib import Path
import tempfile
import os
import sys
# Ensure project root is on sys.path so tests can import broca package when
# run from the repository root.
sys.path.insert(0, os.path.abspath(os.getcwd()))

from broca.world_state.directory_structure import DirectoryStructureGenerator


@st.composite
def tree_struct(draw):
    # generate small directory trees
    depth = draw(st.integers(min_value=1, max_value=3))
    def gen_level(d):
        n_files = draw(st.integers(min_value=0, max_value=3))
        n_dirs = draw(st.integers(min_value=0, max_value=2))
        files = [f"file_{i}.txt" for i in range(n_files)]
        dirs = {}
        for i in range(n_dirs):
            dirs[f"dir_{i}"] = gen_level(d+1) if d < depth else {}
        return {f: None for f in files} | dirs
    return gen_level(0)


@given(tree_struct())
def test_scan_idempotent(struct):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # helper to create
        def make_tree(root, structure):
            for name, value in structure.items():
                if value is None:
                    (root / name).write_text("c")
                else:
                    (root / name).mkdir(parents=True, exist_ok=True)
                    make_tree(root / name, value)
        make_tree(root, struct)
        gen = DirectoryStructureGenerator(str(root))
        files1, dirs1 = gen.scan_directory()
        files2, dirs2 = gen.scan_directory()
        assert files1 == files2
        assert dirs1 == dirs2
