import json
from pathlib import Path

from broca.memory import RelationType


FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "golden_traces" / "memory_replay.json"


def test_memory_manager_replays_golden_trace(memory_manager):
    fixture = json.loads(FIXTURE_PATH.read_text())

    stored_ids = []
    for entry in fixture["memories"]:
        mem_id, _, _ = memory_manager.store_memory(
            namespace=entry["namespace"],
            text=entry["text"],
            importance=entry["importance"],
            tags=entry["tags"],
            auto_link=False,
            deduplicate=False,
        )
        stored_ids.append(mem_id)

    for rel in fixture["relationships"]:
        memory_manager.link_memories(
            stored_ids[rel["source"]],
            stored_ids[rel["target"]],
            RelationType(rel["type"]),
            strength=rel.get("strength", 1.0),
        )

    for query in fixture["queries"]:
        results = memory_manager.retrieve_memories(**query["params"])
        observed_order = [record.text for record in results][: len(query["expected_order"])]
        assert observed_order == query["expected_order"], query["description"]

        expected_relationships = query.get("expected_relationships")
        if expected_relationships:
            target_id = stored_ids[expected_relationships["memory_index"]]
            related = memory_manager.get_related_memories(target_id)
            related_types = {relation.relation_type.value for _, relation in related}
            for relation_type in expected_relationships["relation_types"]:
                assert relation_type in related_types
