import uuid

from app.domain.exceptions import InvalidCredentials, UserAlreadyExists
from app.domain.repositories import SessionRepository, UserRepository
from app.domain.user import Session, User, hash_password, verify_password


class AuthService:
    """Регистрация пользователей и проверка их токенов"""

    def __init__(self, user_repository: UserRepository, session_repository: SessionRepository) -> None:
        self._users = user_repository
        self._sessions = session_repository

    def register(self, username: str, password: str) -> User:
        user = self._users.get_by_username(username)
        if user is not None:
            # повторная регистрация с теми же кредами не ошибка
            if verify_password(password, user.password_hash):
                return user
            raise UserAlreadyExists()

        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password),
        )
        if not self._users.add(user):
            raise UserAlreadyExists()
        return user

    def login(self, username: str, password: str) -> Session:
        user = self._users.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentials()
        session = Session(user_id=user.id)
        self._sessions.add(session)
        return session

    def resolve_token(self, token: str) -> Session | None:
        return self._sessions.get(token)
