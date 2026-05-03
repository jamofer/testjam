"""Unit tests for auth/security.py — no database required."""
import time

import pytest

from testjam.auth.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_and_verify_roundtrip():
    plain = "my-secret-password"

    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed)


def test_wrong_password_does_not_verify():
    hashed = hash_password("correct")

    result = verify_password("wrong", hashed)

    assert result is False


def test_each_hash_is_unique():
    h1 = hash_password("same")
    h2 = hash_password("same")

    assert h1 != h2


def test_create_and_decode_token():
    token = create_access_token("alice")

    subject = decode_token(token)

    assert subject == "alice"


def test_decode_returns_none_for_garbage():
    subject = decode_token("not.a.jwt")

    assert subject is None


def test_decode_returns_none_for_tampered_signature():
    token = create_access_token("alice")
    tampered = token[:-4] + "XXXX"

    subject = decode_token(tampered)

    assert subject is None
