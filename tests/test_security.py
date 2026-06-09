"""Unit tests for shared.security: password hashing and JWT round-trips."""

from datetime import timedelta

from shared import security


def test_password_hash_roundtrip():
    h = security.get_password_hash("s3cret")
    assert h != "s3cret"  # not stored in plaintext
    assert security.verify_password("s3cret", h) is True
    assert security.verify_password("wrong", h) is False


def test_password_hash_is_salted():
    # bcrypt salts each hash, so two hashes of the same password differ.
    assert security.get_password_hash("pw") != security.get_password_hash("pw")


def test_access_token_roundtrip():
    token = security.create_access_token({"sub": "alice"})
    payload = security.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"
    assert "exp" in payload


def test_decode_invalid_token_returns_none():
    assert security.decode_access_token("not-a-jwt") is None


def test_decode_expired_token_returns_none():
    token = security.create_access_token(
        {"sub": "bob"}, expires_delta=timedelta(seconds=-1)
    )
    assert security.decode_access_token(token) is None
