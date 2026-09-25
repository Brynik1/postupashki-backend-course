import hashlib
import time
import uuid


class User:
    """Пользователь сервиса (пригодится с hw2)"""

    def __init__(self, user_id: str, username: str, password_hash: str) -> None:
        self.id = user_id
        self.username = username
        self.password_hash = password_hash

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Session:
    """Сессия аутентифицированного пользователя"""

    def __init__(self, user_id: str, session_id: str | None = None) -> None:
        self.user_id = user_id
        self.session_id = session_id or uuid.uuid4().hex


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
