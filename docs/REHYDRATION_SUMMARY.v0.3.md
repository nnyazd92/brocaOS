# REHYDRATION_SUMMARY v0.3

Boot time: 2025-12-23T04:40:28.760304+00:00

Operator approval: APPROVE+CONFIRM VERIFY
Actuator token provenance: .temporary_token.txt (token_jti: 6e05bdfaae9c4ef1b340b2a3bd4823e4; verified by environment: True)

Identity verification: FAILED
Reasons:
- BROCA_TOKEN_SECRET sensor not found (cannot compute HMAC-SHA256)
- identity.provenance.token_jti (6b761cbbdd614d9c81011c24d54bcd3a) does not match provided actuator token jti (6e05bdfaae9c4ef1b340b2a3bd4823e4)
- fallback verification using .temporary_token.txt not possible due to jti mismatch

Persistence posture: SANDBOXED (persistence_enabled: false)

Session continuity:
- session pointer: docs/artifacts/broca.session.pointer
- loaded session summary: docs/summaries/session-2025-12-23T04-29-59.502401+00-00.json

Actions taken:
- read .temporary_token.txt
- verify token via environment_access (result: valid)
- snapshot repo (pre-boot) - no changes to commit
- built project world state
- read protocol file PROTOCOL.BOOT_UP.v0.3.md
- read session pointer and session summary
- read identity and signature
- attempted signature verification (failed)
- wrote REHYDRATION_SUMMARY.v0.3.json and .md with audit info

Audit:
- version_control_snapshot: No changes to commit
- token_verified: True

Verification re-check: computed HMAC matches signature; token_jti mismatch, persistence remains sandboxed.