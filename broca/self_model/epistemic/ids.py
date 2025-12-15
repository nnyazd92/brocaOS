"""
Knowledge ID generation and management.

Provides utilities for generating unique identifiers for knowledge items
in the self-model (capabilities, constraints, knowledge boundaries, etc.).
"""

from __future__ import annotations

from typing import Dict, Any
import hashlib
import json


# Type alias for knowledge IDs
KnowledgeID = str


def generate_knowledge_id(
    category: str,
    content: str,
    context: Dict[str, Any] | None = None
) -> KnowledgeID:
    """
    Generate a unique knowledge ID from category, content, and optional context.
    
    Args:
        category: Category of knowledge (e.g., "capability", "constraint", "knowledge_boundary")
        content: The actual knowledge content
        context: Optional additional context for uniqueness
        
    Returns:
        Unique knowledge ID string
    """
    # Create a deterministic hash from the inputs
    data = {
        "category": category,
        "content": content,
        "context": context or {},
    }
    
    # Serialize to JSON for hashing (sorted keys for consistency)
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    
    # Generate hash
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 chars for brevity
    
    # Format: category_hash
    return f"{category}_{hash_hex}"


def generate_capability_id(capability: str) -> KnowledgeID:
    """Generate ID for a capability."""
    return generate_knowledge_id("capability", capability)


def generate_constraint_id(constraint_key: str, constraint_value: Any) -> KnowledgeID:
    """Generate ID for a constraint."""
    return generate_knowledge_id("constraint", f"{constraint_key}:{constraint_value}")


def generate_knowledge_boundary_id(boundary_key: str, boundary_value: Any) -> KnowledgeID:
    """Generate ID for a knowledge boundary."""
    return generate_knowledge_id("knowledge_boundary", f"{boundary_key}:{boundary_value}")


def generate_preference_id(preference_key: str, preference_value: Any) -> KnowledgeID:
    """Generate ID for a preference."""
    return generate_knowledge_id("preference", f"{preference_key}:{preference_value}")


def generate_behavioral_pattern_id(pattern: Dict[str, Any]) -> KnowledgeID:
    """Generate ID for a behavioral pattern."""
    pattern_str = json.dumps(pattern, sort_keys=True, ensure_ascii=False)
    return generate_knowledge_id("behavioral_pattern", pattern_str)

