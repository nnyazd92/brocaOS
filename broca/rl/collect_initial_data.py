#!/usr/bin/env python3
"""Collect initial RL experiences by registering a dummy tool and calling it multiple times."""
import json
import time
from broca.tools.registry import ToolRegistry
from broca.tools import Tool

# Create registry
reg = ToolRegistry()

# Define a simple dummy tool
class DummyTool(Tool):
    def __init__(self):
        super().__init__(
            name='dummy_tool',
            description='Dummy tool for RL experience collection',
            parameters={'type':'object','properties':{'x':{'type':'integer'}},'required':['x']}
        )
    def execute(self, x=0):
        # Simulate work
        time.sleep(0.01)
        return {'success': True, 'output': f'ok:{x}'}

# Register and call
reg.register_tool(DummyTool())
for i in range(200):
    tool = reg.get_tool('dummy_tool')
    call = {
        'id': f'ex{i}',
        'type':'function',
        'function':{'name':'dummy_tool','arguments': json.dumps({'x': i})}
    }
    res = reg.execute_tool_call(call)
    if i % 50 == 0:
        print(f'Called dummy_tool {i} times')

print('Done')
