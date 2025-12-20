#!/usr/bin/env python3
import argparse, json, os, re, sys, time
from pathlib import Path

# --------- path discovery ---------
def find_repo_root(start: Path) -> Path:
    p = start
    while p != p.parent:
        if (p / ".git").exists() or (p / "broca").exists() or (p / "BROCA_OPERATORS_GUIDE.md").exists():
            return p
        p = p.parent
    return start

def has_dir(p: Path, rel: str) -> bool:
    return (p / rel).exists() and (p / rel).is_dir()

def pick_docs_root(root: Path) -> Path:
    # Prefer broca/docs if present, else docs at repo root
    if has_dir(root, "broca/docs"):
        return root / "broca/docs"
    return root / "docs"

def pick_operators_guide(root: Path) -> Path:
    if (root / "broca/BROCA_OPERATORS_GUIDE.md").exists():
        return root / "broca/BROCA_OPERATORS_GUIDE.md"
    return root / "BROCA_OPERATORS_GUIDE.md"

def pick_user_schema_dir(root: Path) -> Path:
    # Prefer broca/user/schema
    if has_dir(root, "broca/user"):
        (root / "broca/user/schema").mkdir(parents=True, exist_ok=True)
        return root / "broca/user/schema"
    (root / "user/schema").mkdir(parents=True, exist_ok=True)
    return root / "user/schema"

def pick_user_insights_dir(root: Path) -> Path:
    # Prefer broca/user/insights/generated
    d = root / "broca/user/insights/generated"
    if has_dir(root, "broca/user"):
        d.mkdir(parents=True, exist_ok=True)
        return d
    d2 = root / "user/insights/generated"
    d2.mkdir(parents=True, exist_ok=True)
    return d2

# --------- io helpers ---------
def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def backup_then_write(path: Path, content: str, apply: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    if apply:
        if path.exists():
            bak = path.with_suffix(path.suffix + f".bak_{int(time.time())}")
            path.rename(bak)
            print(f"* backup -> {bak}")
        path.write_text(content, encoding="utf-8")
        print(f"+ wrote {path}")
    else:
        print(f"(dry-run) would write {path}")

def append_block_if_missing(path: Path, marker: str, block: str, apply: bool):
    if not path.exists():
        print(f"! missing file for append: {path} (skipped)")
        return
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if marker in txt:
        print(f"= marker present in {path} ({marker})")
        return
    new_txt = (txt.rstrip() + "\n\n" + block.rstrip() + "\n")
    if apply:
        bak = path.with_suffix(path.suffix + f".bak_{int(time.time())}")
        path.rename(bak)
        path.write_text(new_txt, encoding="utf-8")
        print(f"+ appended block to {path} (backup: {bak.name})")
    else:
        print(f"(dry-run) would append block to {path} (marker: {marker})")

# --------- payloads ---------
SELF_MODEL_POLICY_MD = """Title: Self-Model Update Policy
Rule:
- update_self_model is permitted exactly once per session, only within the Shutdown Protocol.
- Mid-session self-model updates are prohibited.
- Any change to identity/origin/invariants requires the Origin Revision Protocol with explicit provenance before execution.
Required provenance in Shutdown step:
- Plan approval status: approved by <approver> (<reference ID>)
- Actuator token issuance status: issued (issuer/service; reference ID)
- Actuator token provenance: <token ID>; verification method: <registry/log|message ID>; verification location: <concrete anchor>
- Execution status: Executed (only after the above)
Rationale: Minimize contradictions and maximize self-consistency across all layers by synchronizing meta updates at a single canonical point.
"""

HIGH_STAKES_POLICY_MD = """Title: High-Stakes Evaluation Policy
Scope: System modification, invariants/origin changes, escalation/actuators, security/privilege.
Checklist (must complete before execution):
- Problem statement and success criteria
- Risk/impact assessment and artifact map
- Contradiction scan against policies/protocols
- Test plan (TDD) + rollback plan
- Provenance: Plan approval status, Actuator token issuance status, Actuator token provenance (anchored)
- Decision record (include verification anchor)
"""

INSIGHT_SCHEMA = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Insight",
  "type": "object",
  "required": ["id","title","statement","status","created_at"],
  "properties": {
    "id": {"type":"string"},
    "title": {"type":"string"},
    "statement": {"type":"string"},
    "rationale": {"type":"string"},
    "status": {"type":"string","enum":["proposed","accepted","deprecated"]},
    "created_at": {"type":"string","format":"date-time"},
    "updated_at": {"type":"string","format":"date-time"},
    "provenance": {
      "type":"object",
      "properties":{
        "approver":{"type":"string"},
        "reference_id":{"type":"string"},
        "verification":{"type":"object","properties":{
          "method":{"type":"string","enum":["registry/log","message ID"]},
          "location":{"type":"string"}
        },"required":["method","location"]}
      }
    },
    "related_schemas": {
      "type":"array",
      "items":{"type":"object","properties":{
        "relation":{"type":"string","enum":["supports","contradicts","elaborates","supersedes","references"]},
        "target_id":{"type":"string"}
      },"required":["relation","target_id"]}
    },
    "tags":{"type":"array","items":{"type":"string"}}
  }
}

META_SCHEMA = {
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "title":"Meta-Schema",
  "type":"object",
  "properties":{
    "schema_id":{"type":"string"},
    "name":{"type":"string"},
    "version":{"type":"string"},
    "identity_fields":{"type":"array","items":{"type":"string"}},
    "required_fields":{"type":"array","items":{"type":"string"}},
    "relations_supported":{"type":"array","items":{"type":"string"}},
    "crud_rules":{"type":"string"},
    "versioning_policy":{"type":"string"},
    "migration_guidance":{"type":"string"}
  }
}

# Refined test: scan only documentation (md/rst/txt) under docs roots; whitelist allowed files
TEST_POLICY_REFERENCES = """import re
from pathlib import Path

DOC_SUFFIXES = {'.md', '.rst', '.txt'}

def pick_docs_roots(root: Path):
    roots = []
    if (root / 'broca/docs').exists():
        roots.append(root / 'broca/docs')
    if (root / 'docs').exists():
        roots.append(root / 'docs')
    return roots or [root]

def test_no_mid_session_self_model_refs():
    root = Path(__file__).resolve().parents[1]
    docs_roots = pick_docs_roots(root)
    allow = {
        (dr / 'protocols' / 'PROTOCOL.SHUTDOWN.v0.1.md').resolve().as_posix()
        for dr in docs_roots
    } | {
        (dr / 'guidelines' / 'POLICY.SELF_MODEL_UPDATES.v0.1.md').resolve().as_posix()
        for dr in docs_roots
    }
    violations = []
    for dr in docs_roots:
        for p in dr.rglob('*'):
            if p.is_dir(): continue
            if p.suffix.lower() not in DOC_SUFFIXES: continue
            text = p.read_text(encoding='utf-8', errors='ignore')
            if 'update_self_model' in text:
                if p.resolve().as_posix() not in allow:
                    violations.append(p.resolve().as_posix())
    assert not violations, f"update_self_model references outside Shutdown policy/docs: {violations}"
"""

# Insight payload for later ingestion via your middleware
def build_insights_payload():
    t = now_iso()
    return [
      {
        "id": "insight-context-contradictions",
        "title": "Context-contradiction failure mode",
        "statement": "Accumulating contradictions in the context window are a primary failure mode; synchronize meta/self-model updates at Shutdown.",
        "rationale": "Reduce conflicts by consolidating meta updates.",
        "status": "accepted",
        "created_at": t,
        "provenance": {
          "approver": "Nick Yazdani",
          "reference_id": "M1",
          "verification": {"method": "message ID", "location": "call_YgKkgNDxkAu3edX97A3yJPnl"}
        },
        "related_schemas": [],
        "tags": ["insight","context-contradictions","policy","shutdown-only-updates"]
      },
      {
        "id": "insight-meta-schema-graph",
        "title": "Meta-schema graph pattern",
        "statement": "Define a meta-schema for CRUD/linking schemas to form a graph across user/system knowledge and policies.",
        "rationale": "Enable structured relations: supports/contradicts/elaborates/supersedes/references.",
        "status": "proposed",
        "created_at": t,
        "provenance": {
          "approver": "Nick Yazdani",
          "reference_id": "M1",
          "verification": {"method": "message ID", "location": "call_YgKkgNDxkAu3edX97A3yJPnl"}
        },
        "related_schemas": [],
        "tags": ["insight","meta-schema","graph","policy"]
      },
      {
        "id": "pattern-high-stakes-eval",
        "title": "High-stakes evaluation",
        "statement": "Logically and rigorously evaluate high-stakes suggestions (system modifications) with a checklist (TDD, rollback, provenance).",
        "rationale": "Calibrate correctly on risky changes.",
        "status": "accepted",
        "created_at": t,
        "provenance": {
          "approver": "Nick Yazdani",
          "reference_id": "M1",
          "verification": {"method": "message ID", "location": "call_YgKkgNDxkAu3edX97A3yJPnl"}
        },
        "related_schemas": [],
        "tags": ["pattern","high-stakes","evaluation","tdd","rollback","provenance"]
      }
    ]

# --------- main ---------
def main():
    ap = argparse.ArgumentParser(description="Apply policy sync (Shutdown-only self-model updates) + schemas + test")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry run)")
    args = ap.parse_args()

    root = find_repo_root(Path.cwd())
    docs_root = pick_docs_root(root)
    operators_guide = pick_operators_guide(root)
    user_schema_dir = pick_user_schema_dir(root)
    user_insights_dir = pick_user_insights_dir(root)

    # File targets (computed)
    policy_self_model = docs_root / "guidelines" / "POLICY.SELF_MODEL_UPDATES.v0.1.md"
    policy_high_stakes = docs_root / "guidelines" / "POLICY.HIGH_STAKES_EVALUATION.v0.1.md"
    proto_boot = docs_root / "protocols" / "PROTOCOL.BOOT_UP.v0.1.md"
    proto_summary = docs_root / "protocols" / "PROTOCOL.SESSION_SUMMARY.v0.1.md"
    proto_shutdown = docs_root / "protocols" / "PROTOCOL.SHUTDOWN.v0.1.md"

    insight_schema_path = user_schema_dir / "insight.schema.v0.1.json"
    meta_schema_path = user_schema_dir / "meta-schema.schema.v0.1.json"
    insights_payload_path = user_insights_dir / "memory_insights.json"

    test_dir = root / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_policy_refs = test_dir / "test_policy_references.py"

    # Write policy docs and schemas
    backup_then_write(policy_self_model, SELF_MODEL_POLICY_MD, args.apply)
    backup_then_write(policy_high_stakes, HIGH_STAKES_POLICY_MD, args.apply)
    backup_then_write(insight_schema_path, json.dumps(INSIGHT_SCHEMA, indent=2) + "\n", args.apply)
    backup_then_write(meta_schema_path, json.dumps(META_SCHEMA, indent=2) + "\n", args.apply)
    backup_then_write(test_policy_refs, TEST_POLICY_REFERENCES, args.apply)

    # Append markers to operator guide and protocols (if present)
    append_block_if_missing(operators_guide, "BEGIN SELF_MODEL_POLICY", """BEGIN SELF_MODEL_POLICY
Self-model updates (single-source policy)
- Allowed exactly once per session, only during the Shutdown Protocol.
- Mid-session updates are prohibited.
- Identity/origin/invariant changes require the Origin Revision Protocol with provenance.
See: guidelines/POLICY.SELF_MODEL_UPDATES.v0.1.md
Top-level invariant: minimize contradictions; maximize self-consistency across all layers.
END SELF_MODEL_POLICY
""", args.apply)

    append_block_if_missing(proto_boot, "BEGIN NO_SELF_MODEL_BOOT", """BEGIN NO_SELF_MODEL_BOOT
Note: Boot Up does not perform self-model updates. Such updates occur only during Shutdown per policy.
END NO_SELF_MODEL_BOOT
""", args.apply)

    append_block_if_missing(proto_summary, "BEGIN NO_SELF_MODEL_SUMMARY", """BEGIN NO_SELF_MODEL_SUMMARY
Note: Session Summary does not perform self-model updates. See Shutdown policy for update timing.
END NO_SELF_MODEL_SUMMARY
""", args.apply)

    append_block_if_missing(proto_shutdown, "BEGIN SELF_MODEL_UPDATE_STEP", """BEGIN SELF_MODEL_UPDATE_STEP
Self-model update step (policy-compliant):
- Plan approval status: approved by <approver> (<reference ID>)
- Actuator token issuance status: issued (issuer/service: <issuer>; reference ID: <ref>)
- Actuator token provenance: <token ID>; verification method: <registry/log|message ID>; verification location: <anchor>
- Execution status: Executed (only after the above)
END SELF_MODEL_UPDATE_STEP
""", args.apply)

    # Emit insights payload for later ingestion
    backup_then_write(insights_payload_path, json.dumps(build_insights_payload(), indent=2) + "\n", args.apply)

    print("\nDone.")
    print("- Dry run by default; re-run with --apply to write files.")
    print("- Then run: pytest -q tests/test_policy_references.py")
    print("- Prepare a PR with the changes.")
    print("- After merge or when writable, ingest", insights_payload_path)

if __name__ == "__main__":
    main()
