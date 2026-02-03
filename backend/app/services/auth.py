from __future__ import annotations

from itsdangerous import BadSignature, URLSafeSerializer

from app.core.config import settings

_serializer = URLSafeSerializer(settings.secret_key, salt="session")


def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def verify_session_token(token: str) -> int | None:
    try:
        data = _serializer.loads(token)
    except BadSignature:
        return None
    user_id = data.get("user_id")
    return int(user_id) if user_id is not None else None
