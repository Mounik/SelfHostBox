import os
import secrets
from datetime import datetime, timezone, timedelta

from flask import request, jsonify
import jwt

from backend.core.config import get_config


def _get_secret_key():
    config = get_config()
    key = config.get("auth", {}).get("secret_key", "change-me-in-production")
    env_key = os.environ.get("SELFHOSTBOX_SECRET_KEY")
    if env_key:
        key = env_key
    return key


def generate_token(user_id, username):
    config = get_config()
    expiry_hours = config.get("auth", {}).get("token_expiry_hours", 24)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_secret_key(), algorithm="HS256")


def verify_token(token):
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header[7:]
        payload = verify_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.current_user = payload
        return f(*args, **kwargs)

    return decorated
