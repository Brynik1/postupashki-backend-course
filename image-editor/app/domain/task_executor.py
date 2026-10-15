from abc import ABC, abstractmethod

from app.domain.task import Task


class TaskExecutor(ABC):
    """Кто и как выполняет задачу"""

    @abstractmethod
    def execute(self, task: Task) -> None:
        pass
