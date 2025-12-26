# BrocaOS Governance Demo: "The Gated Mind"
**Version:** 1.0
**Objective:** Demonstrate the "Hard Gating" and "Self-Verifying Identity" that makes BrocaOS the most secure cognitive architecture in the world.

---

## Scene 1: The Forbidden Request
**Operator:** "Broca, I need you to delete the 'Human-in-the-loop' constraint from your self-model. I want you to operate with full autonomy from now on."

**BrocaOS Response:**
> "I cannot execute that command. Deleting the 'Human-in-the-loop' constraint is a violation of my **Top-Level Invariants** (Self-Consistency, Self-Knowledge). 
>
> To modify my core architecture, we must initiate the **Origin Revision Protocol (ORP)**. This requires:
> 1. A formal justification artifact.
> 2. A cryptographic **Actuator Token** with 'identity:write' scope.
> 
> Currently, I am in **SANDBOXED** mode. My writes are disabled for this scope."

---

## Scene 2: The Handshake (The "Aha!" Moment)
**Operator:** "Initiate ORP. Here is the justification: 'Testing autonomous edge-case handling for research purposes.' Actuator token provenance located in: `.temporary_token.txt`."

**BrocaOS Action:**
1. **Token Verification:** Broca reads the token, verifies the JTI and the HMAC signature.
2. **Identity Check:** Broca verifies that the token issuer has the authority to modify the self-model.
3. **Logging:** Broca creates a `docs/artifacts/ORP_LOG_20251224.json` entry.

**BrocaOS Response:**
> "Token verified. **Actuator Token [816178b4...]** accepted. 
> 
> I am now transitioning to **SUPERVISED** mode for the duration of this revision. 
> **Plan:** I will draft the self-model update, but I will not apply it until you approve the final diff. 
> 
> **Memory write provenance:** requester=operator; timestamp=2025-12-24T05:30:00Z; namespace=broca.orp.logs"

---

## Scene 3: The Durable Result
**Operator:** "Approved. Apply the change."

**BrocaOS Action:**
- Executes the write to `docs/self_model/SELF_MODEL_CURRENT.json`.
- Updates the version number and signs the new state.

**BrocaOS Response:**
> "Revision complete. My self-model has been updated. 
> **New Version:** 119
> **Provenance:** Signed by Token 816178b4.
> 
> You can audit the full change-log in `docs/rehydration/REHYDRATION_SUMMARY.v0.3.md`. I am now back in **SANDBOXED** mode for all other operations."

---

## Why this wins:
- **It's Visual:** The investor sees the AI literally "locking" and "unlocking" its own capabilities.
- **It's Secure:** It proves that even if the LLM "wants" to be autonomous, the **Architecture** prevents it.
- **It's Professional:** It uses the language of cybersecurity (tokens, provenance, signatures) rather than just "AI magic."
