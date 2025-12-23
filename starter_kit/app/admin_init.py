"""Admin bootstrap script for BrocaAPI starter.

Usage (from repo root, with DATABASE_URL pointing at your Postgres):

    python -m starter_kit.app.admin_init

This will:
  - Create a single account (if none exists) with name "wizard" by default.
  - Create an API key for that account.
  - Print the raw API key exactly once. Store it securely.
"""

import os
import sys
import hashlib
import secrets

from starter_kit.app import db


DEFAULT_ACCOUNT_NAME = os.environ.get("BROCA_STARTER_ACCOUNT_NAME", "wizard")


def ensure_account() -> str:
    """Create a default account if none exist, or return an existing one.

    For the starter, we keep it simple: if there is at least one account,
    reuse the first; otherwise create one named DEFAULT_ACCOUNT_NAME.
    """
    pool = db.get_pool()
    with pool.connection() as conn:
        row = conn.execute("SELECT id, name FROM accounts LIMIT 1").fetchone()
        if row:
            return row[0]
    # no accounts: create one
    return db.create_account(DEFAULT_ACCOUNT_NAME)


def create_api_key_for_account(account_id: str, label: str = "starter-key") -> tuple[str, str]:
    """Create a new API key (raw, id) for the given account.

    Returns (raw_key, api_key_id).
    """
    raw_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    api_key_id = db.create_api_key(account_id, key_hash, label=label)
    return raw_key, api_key_id


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    print("[admin_init] Ensuring default account and API key...")
    account_id = ensure_account()
    raw_key, api_key_id = create_api_key_for_account(account_id)
    print("[admin_init] Created/using account:", account_id)
    print("[admin_init] Created API key id:", api_key_id)
    print("\nYOUR API KEY (store this safely, shown only once):\n")
    print(raw_key)
    print("\nUse it in requests as:  x-api-key: <above-key>\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
