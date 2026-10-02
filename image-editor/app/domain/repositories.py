from abc import ABC, abstractmethod

from app.domain.task import Task
from app.domain.user import Session, User


class TaskRepository(ABC):
    @abstractmethod
    def save(self, task: Task) -> Task: ...

    @abstractmethod
    def get(self, task_id: str) -> Task | None: ...

    @abstractmethod
    def update(self, task: Task) -> None: ...


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> bool: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...


class SessionRepository(ABC):
    @abstractmethod
    def add(self, session: Session) -> None: ...

    @abstractmethod
    def get(self, session_id: str) -> Session | None: ...
