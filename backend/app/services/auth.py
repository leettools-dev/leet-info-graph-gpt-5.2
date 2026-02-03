from __future__ import annotations

import secrets

from itsdangerous import BadSignature, URLSafeSerializer

from app.core.config import settings

def _get_serializer() -> URLSafeSerializer:
    return URLSafeSerializer(settings.secret_key, salt="session")


def create_session_token(user_id: int) -> str:
    return _get_serializer().dumps({"user_id": user_id})


def create_oauth_state(*, request_host: str) -> str:
    # Request host is included to make state tokens environment-specific.
    nonce = secrets.token_urlsafe(24)
    return _get_serializer().dumps({"nonce": nonce, "host": request_host})


def verify_oauth_state(*, token: str, expected_token: str) -> bool:
    try:
        data = _get_serializer().loads(token)
        expected = _get_serializer().loads(expected_token)
    except BadSignature:
        return False
    return data.get("nonce") == expected.get("nonce") and data.get("host") == expected.get(
        "host"
    )


def verify_session_token(token: str) -> int | None:
    try:
        data = _get_serializer().loads(token)
    except BadSignature:
        return None
    user_id = data.get("user_id")
    return int(user_id) if user_id is not None else None
