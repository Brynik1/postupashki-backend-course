import hashlib
import hmac
import secrets
import time

_PBKDF2_ROUNDS = 100_000


class User:
    """Пользователь сервиса"""

    def __init__(self, user_id: str, username: str, password_hash: str) -> None:
        self.id = user_id
        self.username = username
        self.password_hash = password_hash

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Session:
    """Сессия аутентифицированного пользователя с ограниченным сроком жизни"""

    DEFAULT_TTL_SECONDS = 24 * 3600

    def __init__(self, user_id: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.user_id = user_id
        self.session_id = secrets.token_urlsafe(32)
        self.expires_at = time.time() + ttl_seconds

    def expired(self) -> bool:
        return time.time() >= self.expires_at


def hash_password(password: str) -> str:
    # храним вместе с солью, чтобы без перебора по готовым таблицам
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS
    ).hex()
    return f"pbkdf2:{_PBKDF2_ROUNDS}:{salt}:{digest}"


def verify_password(password: str, password_hash: str) -> bool:
    algo, rounds, salt, digest = password_hash.split(":")
    if algo != "pbkdf2":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds)
    ).hex()
    # сравнение по константе, чтобы не подсказывать время угадывания
    return hmac.compare_digest(candidate, digest)
