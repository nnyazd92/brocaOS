import subprocess
import json
import os

def _git_config(key: str):
    try:
        out = subprocess.check_output(["git", "config", key], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None

def _load_profile_file(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception:
        return None

def get_default_identity():
    # Git config first
    name = _git_config("user.name")
    email = _git_config("user.email")

    if name:
        sub = name.lower().replace(" ", ".")
        return {"sub": sub, "name": name, "email": email or ""}
    # Fallback to profile file (if present)
    profile = _load_profile_file("BROCA_PROFILE.json")
    if profile:
        sub = profile.get("sub", "nick.yazdani")
        name = profile.get("name", "Nick Yazdani")
        email = profile.get("email", "")
        return {"sub": sub, "name": name, "email": email}
    # Final fallback
    return {"sub": "nick.yazdani", "name": "Nick Yazdani", "email": ""}

def default_scopes():
    return ["filesystem:write", "project:write", "memory:write"]

def default_expiry_seconds():
    # 5 minutes (per latest plan)
    return 300