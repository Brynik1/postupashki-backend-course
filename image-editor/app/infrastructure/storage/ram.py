import threading

from app.domain.repositories import SessionRepository, TaskRepository, UserRepository
from app.domain.task import Task
from app.domain.user import Session, User


class RamTaskStorage(TaskRepository):
    """RAM-хеш-таблица задач (внутренности легко заменить на БД)"""

    def __init__(self) -> None:
        self._data: dict[str, Task] = {}
        self._lock = threading.Lock()

    def save(self, task: Task) -> Task:
        with self._lock:
            self._data[task.task_id] = task
        return task

    def update(self, task: Task) -> None:
        self.save(task)

    def get(self, task_id: str) -> Task | None:
        return self._data.get(task_id)


class RamUserStorage(UserRepository):
    """index по username + основной хеш id -> User"""

    def __init__(self) -> None:
        self._data: dict[str, User] = {}
        self._by_username: dict[str, User] = {}
        self._lock = threading.Lock()

    def add(self, user: User) -> bool:
        with self._lock:
            if user.username in self._by_username:
                return False
            self._by_username[user.username] = user
            self._data[user.id] = user
            return True

    def get_by_username(self, username: str) -> User | None:
        with self._lock:
            return self._by_username.get(username)


class RamSessionStorage(SessionRepository):
    def __init__(self) -> None:
        self._data: dict[str, Session] = {}
        self._lock = threading.Lock()

    def add(self, session: Session) -> None:
        with self._lock:
            self._data[session.session_id] = session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            return self._data.get(session_id)
