import pytest

from app.services.auth import create_oauth_state, verify_oauth_state


def test_oauth_state_round_trip_ok() -> None:
    a = create_oauth_state(request_host="localhost:8000")
    b = a
    assert verify_oauth_state(token=a, expected_token=b) is True


def test_oauth_state_mismatch_nonce_or_host_fails() -> None:
    a = create_oauth_state(request_host="localhost:8000")
    b = create_oauth_state(request_host="localhost:8000")
    assert verify_oauth_state(token=a, expected_token=b) is False

    c = create_oauth_state(request_host="example.com")
    assert verify_oauth_state(token=a, expected_token=c) is False


def test_oauth_state_bad_signature_fails() -> None:
    token = create_oauth_state(request_host="localhost:8000")
    assert verify_oauth_state(token=token + "x", expected_token=token) is False
