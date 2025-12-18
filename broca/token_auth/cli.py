import argparse
import json
import os
import time
from . import token as token_mod
from .defaults import get_default_identity, default_scopes, default_expiry_seconds

def _load_dotenv():
    dotenv_path = ".env"
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k not in os.environ:
                os.environ[k] = v

def main():
    _load_dotenv()
    parser = argparse.ArgumentParser(prog="broca-token", add_help=True)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a JWT-like token with defaults")
    gen.add_argument("--name", help="Display name for the token (default autofill)")
    gen.add_argument("--sub", help="Subject identifier (default autofill)")
    gen.add_argument("--scopes", help="Comma-separated scopes (default autofill)")
    gen.add_argument("--expiry-seconds", type=int, help="Expiry in seconds (default 300)")
    gen.add_argument("--expiry-iso", help="Expiry as ISO timestamp (optional)")
    gen.add_argument("--purpose", help="Optional purpose text")

    args = parser.parse_args()

    if args.command != "generate":
        print("Only 'generate' is implemented in this skeleton.", flush=True)
        return

    identity = get_default_identity()
    sub = args.sub or identity.get("sub")
    name = args.name or identity.get("name", "")
    secret_key = os.environ.get("BROCA_TOKEN_SECRET")

    if not secret_key:
        # Try to load from .env (already loaded into env by _load_dotenv)
        secret_key = os.environ.get("BROCA_TOKEN_SECRET")

    scopes = []
    if args.scopes:
        scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
    else:
        scopes = default_scopes()

    expiry_seconds = args.expiry_seconds if args.expiry_seconds is not None else default_expiry_seconds()

    token_str, payload = token_mod.generate_token(
        sub=sub,
        name=name,
        scopes=scopes,
        expiry_seconds=expiry_seconds,
        secret_key=secret_key if secret_key else "",
        iss="broca-token-v1",
        aud="broca-os",
    )

    output = {"token": token_str, "payload": payload}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()