"""
Efficiency and cost-optimization rules for BrocaOS (Recursive Funding Phase).
"""

from .production_rules import ProductionRule, RuleType

EFFICIENCY_RULES = [
    ProductionRule(
        name="prevent_redundant_list_dir",
        rule_type=RuleType.CONSTRAIN,
        priority=2.0,
        conditions=[
            {"type": "tool_call_intent", "tool": "LIST_DIR", "path": "$path"},
            {"type": "memory_item", "content": {"tool": "LIST_DIR", "path": "$path", "timestamp": "$recent"}}
        ],
        actions=[
            {"type": "cancel_tool_call", "reason": "Redundant LIST_DIR. Data already in working memory."},
            {"type": "log_efficiency_gain", "metric": "token_savings", "value": 50}
        ]
    ),
    ProductionRule(
        name="prevent_redundant_read_file",
        rule_type=RuleType.CONSTRAIN,
        priority=2.0,
        conditions=[
            {"type": "tool_call_intent", "tool": "READ_FILE", "path": "$path"},
            {"type": "memory_item", "content": {"tool": "READ_FILE", "path": "$path", "timestamp": "$recent"}}
        ],
        actions=[
            {"type": "cancel_tool_call", "reason": "Redundant READ_FILE. Data already in working memory."},
            {"type": "log_efficiency_gain", "metric": "token_savings", "value": 200}
        ]
    ),
    ProductionRule(
        name="gate_expensive_web_search",
        rule_type=RuleType.CONSTRAIN,
        priority=1.5,
        conditions=[
            {"type": "tool_call_intent", "tool": "WEB_SEARCH"},
            {"type": "interoceptive_state", "uncertainty": {"$gt": 0.7}}
        ],
        actions=[
            {"type": "require_verification", "reason": "High uncertainty. Verify search query relevance before execution."},
            {"type": "log_efficiency_gain", "metric": "risk_mitigation", "value": 1.0}
        ]
    ),
    ProductionRule(
        name="summarize_memory_on_pressure",
        rule_type=RuleType.ACTION,
        priority=3.0,
        conditions=[
            {"type": "system_metric", "memory_pressure": {"$gt": 0.8}}
        ],
        actions=[
            {"type": "trigger_tool", "tool": "SUMMARIZE_WORKING_MEMORY"},
            {"type": "log_efficiency_gain", "metric": "context_window_optimization", "value": 0.2}
        ]
    )
]
