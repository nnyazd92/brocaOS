#!/usr/bin/env python3
import argparse, sys, os, datetime
from pathlib import Path

ROOT = Path("/home/wizard/broca")
OUT_DIR = ROOT / "logs" / "shutdown"
WHITELIST_METHODS = {"embedded Escalation block", "file artifact", "registry/log", "message ID"}

def iso(ts=None):
    dt = datetime.datetime.now(datetime.timezone.utc) if ts is None else ts
    return dt.strftime("%Y%m%dT%H%M%SZ")

def validate_verification(method, location, for_issuance=False):
    if method not in WHITELIST_METHODS:
        raise ValueError(f"verification method must be one of {sorted(WHITELIST_METHODS)}")
    if not location or location.strip().lower() in {"n/a", "tbd"}:
        raise ValueError("verification location must be a concrete anchor")
    if method == "message ID" and not location.lower().startswith("message id: "):
        raise ValueError("when method is 'message ID', location must be 'message ID: <specific-ID>'")
    if for_issuance and method not in {"registry/log", "message ID", "embedded Escalation block"}:
        raise ValueError("token issuance verification must be 'registry/log' or 'message ID' (or bind to an embedded Escalation block)")
    return True

def std_block(plan_approval_status, token_line, token_prov, mode_override_line, executed):
    lines = []
    lines.append("Plan: • Close out open threads • Freeze state • Generate REPORT and COMPLETE artifacts")
    lines.append(plan_approval_status)
    lines.append(token_line)
    lines.append(token_prov)
    if mode_override_line:
        lines.append(mode_override_line)
    lines.append(f"Execution status: {'Executed' if executed else 'Not executed'}")
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser(description="Shutdown Protocol helper. Default: dry-run (no writes). Use --apply to write artifacts with a compliant standardized block.")
    ap.add_argument("--apply", action="store_true", help="Perform writes (requires token issuance and whitelisted verification anchor)")
    ap.add_argument("--approver", default="operator/user", help="Plan approver identity")
    ap.add_argument("--approval-ref", default="", help="Plan approval reference ID (required for approved status)")
    ap.add_argument("--plan-status", choices=["approved","pending","denied"], default="pending")

    # Token issuance/provenance
    ap.add_argument("--token-issuer", default="", help="Actuator token issuer/service")
    ap.add_argument("--token-ref", default="", help="Actuator token reference/transaction ID")
    ap.add_argument("--token-id", default="", help="Actuator token ID")
    ap.add_argument("--verification-method", default="", help="Verification method (whitelisted)")
    ap.add_argument("--verification-location", default="", help="Verification location (concrete anchor)")

    # Mode override line (only if read_only/SANDBOXED was overridden)
    ap.add_argument("--mode-before", default="", help="Access level before override (e.g., SANDBOXED)")
    ap.add_argument("--mode-after", default="", help="Access level after override (e.g., SUPERVISED)")
    ap.add_argument("--mode-issuer", default="", help="Mode override issuance authority")
    ap.add_argument("--mode-ver-method", default="", help="Mode override verification method")
    ap.add_argument("--mode-ver-location", default="", help="Mode override verification location")
    ap.add_argument("--mode-rollback", default="", help="Mode override rollback criteria")

    args = ap.parse_args()
    ts = iso()
    report = OUT_DIR / f"SHUTDOWN_REPORT_{ts}.md"
    complete = OUT_DIR / f"SHUTDOWN_COMPLETE_{ts}.md"

    # Plan approval line
    if args.plan_status == "approved":
        if not args.approval_ref:
            print("error: approved plan requires a non-placeholder approval reference ID", file=sys.stderr)
            sys.exit(2)
        plan_line = f"Plan approval status: approved by {args.approver} ({args.approval_ref})"
    elif args.plan_status == "denied":
        plan_line = f"Plan approval status: denied by {args.approver} ({args.approval_ref or 'n/a'})"
    else:
        plan_line = f"Plan approval status: pending by {args.approver} ({'message ID: ' + args.approval_ref if args.approval_ref else 'n/a'})"

    # Token issuance status + provenance
    issued = bool(args.apply)
    if issued:
        if not (args.token_issuer and args.token_ref and args.token_id and args.verification_method and args.verification_location):
            print("error: --apply requires token issuer/ref/id and verification method/location", file=sys.stderr)
            sys.exit(2)
        validate_verification(args.verification_method, args.verification_location, for_issuance=True)
        token_line = f"Actuator token issuance status: issued (issuer/service: {args.token_issuer}; reference ID: {args.token_ref})"
        token_prov = f"Actuator token provenance: token ID: {args.token_id}; verification method: {args.verification_method}; verification location: {args.verification_location}"
    else:
        token_line = "Actuator token issuance status: not issued (issuer/service: n/a; reference ID: n/a)"
        token_prov = "Actuator token provenance: token ID: none/pending; verification method: n/a; verification location: n/a"

    # Mode override (optional)
    mode_line = ""
    if args.mode_before or args.mode_after or args.mode_issuer or args.mode_ver_method or args.mode_ver_location or args.mode_rollback:
        if not (args.mode_before and args.mode_after and args.mode_issuer and args.mode_ver_method and args.mode_ver_location):
            print("error: incomplete mode override line; provide before/after/issuer/ver-method/ver-location", file=sys.stderr)
            sys.exit(2)
        validate_verification(args.mode_ver_method, args.mode_ver_location, for_issuance=False)
        mode_line = (
            f"Access level/mode override: before={args.mode_before} after={args.mode_after}; "
            f"issuance authority={args.mode_issuer}; verification method={args.mode_ver_method}; "
            f"verification location={args.mode_ver_location}; rollback criteria={args.mode_rollback or 'n/a'}"
        )

    block = std_block(plan_line, token_line, token_prov, mode_line, executed=issued)

    if not args.apply:
        print("# Shutdown (dry-run)\n")
        print(block)
        print("(dry-run; no writes performed)")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report.write_text("# Shutdown Report\n\n" + block)
    complete.write_text("# Shutdown Complete\n\n" + block + f"\nReport: {report}\n")
    print(f"Wrote: {report}")
    print(f"Wrote: {complete}")

if __name__ == "__main__":
    main()
