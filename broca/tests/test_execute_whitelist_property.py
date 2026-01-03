from __future__ import annotations

import tempfile

from hypothesis import given, strategies as st

from broca.config import config
from broca.tools.primitive_io import ExecuteTool


@given(
    # Mix in common bypass operators; keep short so the test runs fast.
    op=st.sampled_from(["|", "&&", "||", ";", ">", "<", "$(", "`", "&"]),
    noise=st.text(min_size=0, max_size=30),
)
def test_execute_whitelist_rejects_shell_operators_when_whitelist_enabled(op, noise):
    old = getattr(config.tools, "execute_command_whitelist", [])
    try:
        setattr(config.tools, "execute_command_whitelist", ["python3"])
        tool = ExecuteTool()

        # Construct a command that *appears* to start with an allowed base command.
        cmd = f"python3 -c 'print(1)' {op} {noise}".strip()
        with tempfile.TemporaryDirectory() as td:
            res = tool.execute(cmd=cmd, cwd=str(td), timeout=5, env_allowlist=["PATH"])

        # Should never succeed when chaining/shell constructs are present under whitelist mode.
        assert res.get("success") is False
        assert res.get("error") == "command_not_allowed"
    finally:
        setattr(config.tools, "execute_command_whitelist", old)


