import json

from broca.reasoning.goal_manager import Goal, GoalManager, GoalType
from broca.reasoning.state_manager import ReasoningStateManager


def test_reasoning_state_manager_serializes_goaltype_in_metadata(tmp_path):
    """
    Regression: ReasoningStateManager.save_state must not fail when Goal.metadata contains enums
    (e.g., GoalType). This previously raised:
      "Object of type GoalType is not JSON serializable"
    and could break persistence after restarts.
    """
    state_path = tmp_path / "reasoning_state.json"
    sm = ReasoningStateManager(state_file_path=str(state_path), backup_enabled=False)

    gm = GoalManager()
    gm.add_goal(
        Goal(
            name="goal_with_enum_metadata",
            description="Test goal metadata enum serialization",
            metadata={
                "nested": {"goal_type": GoalType.EXPLORE},
                "also_list": [GoalType.LEARN, GoalType.ACHIEVE],
            },
        )
    )

    assert sm.save_state(goal_manager=gm, force=True) is True

    data = json.loads(state_path.read_text(encoding="utf-8"))
    goals = data["goal_manager"]["goals"]
    goal = next(g for g in goals if g["name"] == "goal_with_enum_metadata")
    assert goal["metadata"]["nested"]["goal_type"] == "explore"
    assert goal["metadata"]["also_list"] == ["learn", "achieve"]
