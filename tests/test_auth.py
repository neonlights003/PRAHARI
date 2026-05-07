"""
Tests for JWT admin auth and bcrypt password hashing.
No external services (Gemini, Cloudinary, DB) are required — these are pure-unit tests.
"""

import os
import time
import pytest
import bcrypt
import jwt as pyjwt
from datetime import datetime, timezone, timedelta

# Set minimal env before importing app modules
os.environ.setdefault("ADMIN_ID", "ci_admin")
os.environ.setdefault("ADMIN_PASSWORD", "ci_password_secure")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret_32_chars_long_ok")

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"


# ── JWT helpers ───────────────────────────────────────────────────────────────

def make_token(sub: str = "ci_admin", role: str = "admin", hours: int = 8) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=hours),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ── JWT tests ─────────────────────────────────────────────────────────────────

def test_jwt_token_encodes_correctly():
    token = make_token()
    assert isinstance(token, str)
    assert token.count(".") == 2  # header.payload.signature


def test_jwt_token_decodes_correctly():
    token = make_token(sub="ci_admin", role="admin")
    payload = decode_token(token)
    assert payload["sub"] == "ci_admin"
    assert payload["role"] == "admin"


def test_jwt_token_expires():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "ci_admin",
        "role": "admin",
        "iat": now,
        "exp": now - timedelta(seconds=1),  # already expired
    }
    expired_token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_jwt_invalid_signature_rejected():
    token = make_token()
    tampered = token[:-4] + "xxxx"
    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_token(tampered)


def test_jwt_wrong_secret_rejected():
    token = make_token()
    with pytest.raises(pyjwt.InvalidSignatureError):
        pyjwt.decode(token, "wrong_secret", algorithms=[JWT_ALGORITHM])


def test_jwt_exp_is_in_future():
    token = make_token(hours=8)
    payload = decode_token(token)
    assert payload["exp"] > time.time()


# ── bcrypt tests ──────────────────────────────────────────────────────────────

def test_bcrypt_hash_and_verify():
    password = "TestPassword123!"
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    assert bcrypt.checkpw(password_bytes, hashed)


def test_bcrypt_wrong_password_rejected():
    password = "CorrectPassword!"
    wrong = "WrongPassword!"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10))
    assert not bcrypt.checkpw(wrong.encode(), hashed)


def test_bcrypt_stored_as_string_roundtrip():
    """Simulates storing hash as TEXT in Postgres then re-encoding for verification."""
    password = "RoundtripTest123"
    hashed_bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10))
    stored_str = hashed_bytes.decode("utf-8")          # store to DB as TEXT
    retrieved_bytes = stored_str.encode("utf-8")        # read back from DB
    assert bcrypt.checkpw(password.encode(), retrieved_bytes)


def test_bcrypt_unicode_password():
    password = "पासवर्ड123"  # Hindi characters — government users may type these
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(10))
    assert bcrypt.checkpw(password.encode("utf-8"), hashed)


# ── Rate limiting config sanity ───────────────────────────────────────────────

def test_slowapi_importable():
    """Verify slowapi package is present in the environment."""
    import importlib.util
    spec = importlib.util.find_spec("slowapi")
    assert spec is not None, "slowapi not installed — add it to requirements.txt"


def test_pyjwt_importable():
    """Verify PyJWT is installed."""
    import jwt  # noqa: F401
    assert hasattr(jwt, "encode") and hasattr(jwt, "decode")
