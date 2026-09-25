import random
import time
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from app.domain.repositories import TaskRepository
from app.domain.task import Task, TaskStatus


class TaskExecutor(ABC):
    """Кто и как выполняет задачу (в hw3 станет очередью RabbitMQ)"""

    @abstractmethod
    def execute(self, task: Task) -> None:
        pass


class LocalImageProcessor(TaskExecutor):
    """Пока выполняет все задачи в потоках этого же процесса"""

    def __init__(
        self,
        task_repository: TaskRepository,
        min_work_seconds: float = 2.0,
        max_work_seconds: float = 5.0,
        workers: int = 8,
    ) -> None:
        self._task_repository = task_repository
        self._min_seconds = min_work_seconds
        self._max_seconds = max_work_seconds
        self._executor = ThreadPoolExecutor(max_workers=workers)

    def execute(self, task: Task) -> None:
        # имитация тяжелой работы с картинкой
        self._executor.submit(self._process, task)

    def _process(self, task: Task) -> None:
        time.sleep(random.uniform(self._min_seconds, self._max_seconds))
        task.status = TaskStatus.ready
        task.result = f"processed image: naive-negative-{uuid.uuid4().hex}.png"
        self._task_repository.update(task)
