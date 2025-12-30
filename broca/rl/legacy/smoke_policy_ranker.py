#!/usr/bin/env python3
import json
from broca.rl.policy import PolicyRanker
from broca.tools.registry import ToolRegistry

# Create a fake context using the provided RL signals
context = {
    'rl_signals': {
        'composite_reward': 0.543374197521958,
        'dissonance_reward': 0.6739979798869857,
        'surprise_reward': 0.9902881783050947,
        'curiosity_reward': 0.3033827988090632,
        'information_gain_reward': 0.06005733987334387,
        'coherence_reward': 0.48954671434686114,
        'exploration_balance': 0.20198651561936673,
    }
}

# Instantiate registry and get tool prototypes
reg = ToolRegistry()
# Use existing registered tools if any; otherwise construct mock objects
all_tools = reg.list_tools()
if not all_tools:
    # Construct mock tool objects
    class MockTool:
        def __init__(self, name):
            self.name=name
            self.description='mock'
            self.parameters={'type':'object','properties':{}}
    all_tools = [MockTool('terminal'), MockTool('web_search'), MockTool('store_memory')]

pr = PolicyRanker()
pr.load_model(None)
probs = pr.predict_distribution(context, all_tools)

# Validate and save
s = sum(probs.values())
print('sum probs =', s)
Path('data/rl').mkdir(parents=True, exist_ok=True)
open('data/rl/policy_smoke.json','w').write(json.dumps({'probs':probs,'sum':s}, indent=2))
print('wrote data/rl/policy_smoke.json')
