import pytest
from broca.rl.policy import PolicyRanker
from broca.tools.selection_guidance import GuidanceAggregator

class MockTool:
    def __init__(self,name):
        self.name=name


def test_policy_ranker_integration():
    tools=[MockTool('terminal'), MockTool('web_search'), MockTool('store_memory')]
    pr=PolicyRanker()
    pr.load_model(None)
    ga=GuidanceAggregator(policy_ranker=pr)
    context={'rl_signals':{'composite_reward':0.5}}
    rankings=ga.get_policy_rankings(tools, context)
    assert isinstance(rankings, list)
    assert all(hasattr(r,'tool_name') for r in rankings)
    total = sum(r.score for r in rankings)
    # allow small numeric tolerance
    assert abs(total - 1.0) < 1e-6

