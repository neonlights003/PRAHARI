import jwt as pyjwt
import secrets
from datetime import datetime, timezone, timedelta

secret = secrets.token_hex(32)
payload = {
    "sub": "admin",
    "role": "admin",
    "iat": datetime.now(timezone.utc),
    "exp": datetime.now(timezone.utc) + timedelta(hours=8),
}
try:
    token = pyjwt.encode(payload, secret, algorithm="HS256")
    print("JWT encode SUCCESS")
    print("Token type:", type(token))
    print("Token:", token[:40], "...")
except Exception as e:
    print("JWT encode FAILED:", type(e).__name__, e)
