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
