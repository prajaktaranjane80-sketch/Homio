import hashlib, json

def mission_fingerprint(mission: dict) -> str:
    payload = json.dumps(mission, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()
