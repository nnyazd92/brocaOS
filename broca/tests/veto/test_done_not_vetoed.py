from __future__ import annotations

from broca.tools.registry import ToolRegistry
from broca.tools.primitive_toolset import DoneTool
from broca.veto.guard import VetoDecision


class _AlwaysVetoGuard:
    def build_time_slice(self, **kwargs):
        return [0.0] * 12

    def check(self, *, x_t, reason: str, kappa_last: float, kappa_integrated: float) -> VetoDecision:
        return VetoDecision(
            veto=True,
            reason=reason,
            threshold=1.0,
            kappa_integrated=float(kappa_integrated),
            kappa_last=float(kappa_last),
            debug={"threshold_mode": "residual", "forced": True},
        )


def _tool_call(call_id: str, name: str, args: str = "{}") -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": args}}


def test_done_is_never_vetoed(monkeypatch):
    import broca.tools.registry as registry_mod

    monkeypatch.setattr(registry_mod, "get_veto_guard", lambda: _AlwaysVetoGuard())

    reg = ToolRegistry()
    reg._governance_engine = None  # type: ignore[attr-defined]
    reg.register_tool(DoneTool())

    res = reg.execute_tool_call(_tool_call("call_done_1", "DONE"))
    assert isinstance(res, dict)
    assert res.get("_veto") is not True
    # DONE should still latch force-final-response state.
    assert bool(getattr(reg, "force_final_response", False)) is True


