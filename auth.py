import base64, hashlib, hmac, json, time
from . import config

def _b64(b: bytes) -> str: return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def _unb64(s: str) -> bytes: return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def create_token(sub: str, ttl: int = 86400) -> str:
    h = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    p = _b64(json.dumps({"sub": sub, "exp": int(time.time()) + ttl}).encode())
    sig = _b64(hmac.new(config.JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

def verify_token(token: str):
    try:
        h, p, s = token.split(".")
        exp = _b64(hmac.new(config.JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(s, exp): return None
        payload = json.loads(_unb64(p))
        return payload if payload["exp"] > time.time() else None
    except Exception:
        return None
