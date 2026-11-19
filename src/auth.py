import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from typing import Any


TEACHERS_FILE = Path(__file__).with_name("teachers.json")
SESSION_TTL_SECONDS = 8 * 60 * 60
PASSWORD_HASH_ITERATIONS = 310_000
_active_sessions: dict[str, tuple[str, float]] = {}


class TeacherCredentialsNotConfigured(Exception):
    pass


def _password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    ).hex()


def set_teacher_password(
    username: str, password: str, credentials_path: Path = TEACHERS_FILE
) -> None:
    username = username.strip().lower()
    if not username:
        raise ValueError("Username cannot be empty.")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")

    teachers: list[dict[str, str]] = []
    if credentials_path.exists():
        data: Any = json.loads(credentials_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("teachers"), list):
            raise ValueError("Teacher credentials file must contain a teachers list.")
        if any(not isinstance(teacher, dict) for teacher in data["teachers"]):
            raise ValueError("Teacher credentials file contains an invalid entry.")
        teachers = data["teachers"]

    salt = secrets.token_bytes(16)
    record = {
        "username": username,
        "salt": salt.hex(),
        "password_hash": _password_hash(password, salt),
    }
    teachers = [teacher for teacher in teachers if teacher.get("username") != username]
    teachers.append(record)

    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = credentials_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps({"teachers": teachers}, indent=2) + "\n", encoding="utf-8"
    )
    temporary_path.chmod(0o600)
    temporary_path.replace(credentials_path)


def authenticate_teacher(
    username: str, password: str, credentials_path: Path = TEACHERS_FILE
) -> bool:
    try:
        data: Any = json.loads(credentials_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise TeacherCredentialsNotConfigured from error

    if not isinstance(data, dict) or not isinstance(data.get("teachers"), list):
        raise ValueError("Teacher credentials file must contain a teachers list.")

    normalized_username = username.strip().lower()
    teacher = next(
        (
            entry
            for entry in data["teachers"]
            if isinstance(entry, dict) and entry.get("username") == normalized_username
        ),
        None,
    )
    if teacher is None:
        return False

    try:
        salt = bytes.fromhex(teacher["salt"])
        expected_hash = teacher["password_hash"]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Teacher credentials file contains an invalid entry.") from error

    actual_hash = _password_hash(password, salt)
    return hmac.compare_digest(actual_hash, expected_hash)


def create_teacher_session(username: str, now: float | None = None) -> str:
    current_time = time.time() if now is None else now
    expired_tokens = [
        token
        for token, (_, expires_at) in _active_sessions.items()
        if expires_at <= current_time
    ]
    for token in expired_tokens:
        del _active_sessions[token]

    token = secrets.token_urlsafe(32)
    _active_sessions[token] = (username, current_time + SESSION_TTL_SECONDS)
    return token


def get_teacher_session(token: str | None, now: float | None = None) -> str | None:
    if not token:
        return None

    session = _active_sessions.get(token)
    if session is None:
        return None

    current_time = time.time() if now is None else now
    username, expires_at = session
    if expires_at <= current_time:
        del _active_sessions[token]
        return None

    return username


def revoke_teacher_session(token: str | None) -> None:
    if token:
        _active_sessions.pop(token, None)
