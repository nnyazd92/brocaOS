#!/usr/bin/env python3
"""
Test the reasoning system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broca.reasoning.production_rules import ProductionRule, ProductionRuleSystem, RuleType
from broca.reasoning.working_memory import WorkingMemory
from broca.reasoning.goal_manager import GoalManager, Goal, GoalStatus, GoalType
from broca.reasoning.integration_tool import ReasoningTool

def test_working_memory():
    """Test working memory functionality."""
    print("=== Testing Working Memory ===")
    
    wm = WorkingMemory(capacity=5)
    
    # Add items
    wm.add({"type": "fact", "content": "The sky is blue", "source": "knowledge"})
    wm.add({"type": "goal", "name": "test_goal", "status": "active"})
    wm.add({"type": "memory", "content": "Working memory test", "tags": ["test"]})
    
    # Retrieve items
    items = wm.retrieve()
    print(f"Retrieved {len(items)} items from working memory")
    for item in items:
        print(f"  - {item.get('type')}: {item.get('content', item.get('name', 'no content'))}")
    
    # Retrieve with pattern
    goal_items = wm.retrieve({"type": "goal"})
    print(f"Retrieved {len(goal_items)} goal items")
    
    # Add a goal
    wm.add_goal({"name": "test_wm_goal", "description": "Test goal in WM", "status": "active"})
    print(f"Active goals in WM: {len(wm.get_active_goals())}")
    
    # Queue a tool call
    wm.queue_tool_call("terminal", {"command": "echo 'test'"})
    queued = wm.get_queued_tools()
    print(f"Queued tools: {len(queued)}")
    
    return wm

def test_production_rules():
    """Test production rule system."""
    print("\n=== Testing Production Rules ===")
    
    # Create a rule
    rule = ProductionRule(
        name="test_rule",
        conditions=[
            {"type": "fact", "content": "The sky is blue"}
        ],
        actions=[
            {
                "type": "add_to_memory",
                "content": {
                    "type": "inference",
                    "content": "Therefore it's daytime",
                    "source": "rule_inference"
                }
            }
        ],
        rule_type=RuleType.INFERENCE,
        priority=1.0
    )
    
    print(f"Created rule: {rule.name}")
    print(f"  Conditions: {len(rule.conditions)}")
    print(f"  Actions: {len(rule.actions)}")
    
    # Test rule system
    rule_system = ProductionRuleSystem()
    print(f"Default rules in system: {len(rule_system.rules)}")
    
    # Add custom rule
    rule_system.add_rule(rule)
    print(f"Total rules after adding: {len(rule_system.rules)}")
    
    # Execute a cycle
    results = rule_system.execute_cycle()
    print(f"Rule cycle executed, fired {len(results)} rules")
    
    return rule_system

def test_goal_manager():
    """Test goal management."""
    print("\n=== Testing Goal Manager ===")
    
    gm = GoalManager()
    
    # Get default goals
    active_goals = gm.get_active_goals()
    print(f"Default active goals: {len(active_goals)}")
    for goal in active_goals:
        print(f"  - {goal.name}: {goal.description} (priority: {goal.priority})")
    
    # Add a new goal
    new_goal = Goal(
        name="test_custom_goal",
        description="Test custom goal for demonstration",
        goal_type=GoalType.ACHIEVE,
        priority=0.8,
        dependencies=["implement_cognitive_reasoning"]
    )
    
    gm.add_goal(new_goal)
    print(f"Added custom goal: {new_goal.name}")
    
    # Get ready goals
    ready_goals = gm.get_ready_goals()
    print(f"Ready goals: {len(ready_goals)}")
    
    # Update progress
    gm.update_goal_progress("implement_cognitive_reasoning", 0.25, "Made progress on implementation")
    goal = gm.get_goal("implement_cognitive_reasoning")
    if goal:
        print(f"Updated goal progress: {goal.name} -> {goal.progress:.2f}")
    
    return gm

def test_integration_tool():
    """Test integration tool."""
    print("\n=== Testing Integration Tool ===")
    
    tool = ReasoningTool()
    
    # Get state
    state_result = tool.execute("get_state")
    if state_result.get("success"):
        state = state_result["state"]
        print(f"Working memory size: {state['working_memory_size']}")
        print(f"Active goals: {state['active_goals_count']}")
        print(f"Ready goals: {state['ready_goals_count']}")
    
    # Add a rule via tool
    rule_data = {
        "name": "tool_added_rule",
        "conditions": [
            {"type": "test", "value": "test_condition"}
        ],
        "actions": [
            {
                "type": "log_message",
                "message": "Test rule fired from tool"
            }
        ],
        "rule_type": "inference",
        "priority": 1.0
    }
    
    add_result = tool.execute("add_rule", rule=rule_data)
    print(f"Add rule result: {add_result.get('success', False)}")
    
    # List rules
    list_result = tool.execute("list_rules")
    if list_result.get("success"):
        print(f"Total rules: {list_result['count']}")
    
    # Add to memory
    memory_result = tool.execute("add_to_memory", memory_content={
        "type": "test",
        "value": "test_content",
        "source": "test_integration"
    })
    print(f"Add to memory result: {memory_result.get('success', False)}")
    
    # Execute cycle
    cycle_result = tool.execute("execute_cycle", max_rules=3)
    if cycle_result.get("success"):
        print(f"Cycle executed: {cycle_result['message']}")
    
    return tool

def main():
    """Run all tests."""
    print("Starting reasoning system tests...\n")
    
    try:
        wm = test_working_memory()
        rule_system = test_production_rules()
        gm = test_goal_manager()
        tool = test_integration_tool()
        
        print("\n=== All Tests Passed ===")
        print(f"Working Memory: {len(wm.items)} items")
        print(f"Production Rules: {len(rule_system.rules)} rules")
        print(f"Goals: {len(gm.get_active_goals())} active goals")
        print(f"Integration Tool: Ready")
        
        return True
        
    except Exception as e:
        print(f"\n=== Test Failed ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
