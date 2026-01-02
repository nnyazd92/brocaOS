from .production_rules import ProductionRule, RuleType

def get_affective_rules():
    """Returns the default affective-triggered production rules."""
    return [
        ProductionRule(
            name="high_dissonance_regulation",
            conditions=[
                {"type": "affective_state", "dissonance": {"$gt": 0.7}}
            ],
            actions=[
                {"type": "trigger_tool", "tool": "SOLVE", "arguments": {"problem": "Resolve high cognitive dissonance detected in internal state."}}
            ],
            rule_type=RuleType.ACTION,
            priority=2.0,
            strength=1.0
        ),
        ProductionRule(
            name="high_curiosity_exploration",
            conditions=[
                {"type": "affective_state", "curiosity": {"$gt": 0.8}}
            ],
            actions=[
                {"type": "trigger_tool", "tool": "WEB_SEARCH", "arguments": {"query": "latest developments in cognitive architecture and self-improving AI"}}
            ],
            rule_type=RuleType.ACTION,
            priority=1.5,
            strength=1.0
        )
    ]
