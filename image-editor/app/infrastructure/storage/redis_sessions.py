import time
import uuid

from app.domain.repositories import SessionRepository
from app.domain.user import Session

_PREFIX = "session:"


class RedisSessionStorage(SessionRepository):
    """Сессии в Redis; TTL берется на себя (EXPIRE), протухшее само пропадет"""

    def __init__(self, client) -> None:
        self._client = client

    @staticmethod
    def _key(session_id: str) -> str:
        return _PREFIX + session_id

    def add(self, session: Session) -> None:
        ttl = max(1, int(session.expires_at - time.time()))
        self._client.setex(self._key(session.session_id), ttl, session.user_id)

    def get(self, session_id: str) -> Session | None:
        user_id = self._client.get(self._key(session_id))
        if user_id is None:
            return None
        # остаток ttl до протухания возвращаем как expires_at сессии
        remaining = self._client.ttl(self._key(session_id))
        session = Session(user_id=user_id)
        session.expires_at = time.time() + max(0, remaining)
        return session

    def delete(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))
