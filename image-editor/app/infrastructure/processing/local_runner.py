import base64
import binascii
import random
import time
from concurrent.futures import ThreadPoolExecutor

from app.domain.repositories import TaskRepository
from app.domain.task import Task, TaskStatus
from app.domain.task_executor import TaskExecutor

# миниатюрная валидная png-картинка 1x1 на случай, если в таске нет изображения
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


class LocalImageProcessor(TaskExecutor):
    """Режим без брокера: выполняет задачи в потоках этого же процесса"""

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
        # сначала result, потом статус: между ними никто не увидит ready без результата
        task.result = self._fake_result(task)
        task.status = TaskStatus.ready
        self._task_repository.update(task)

    @staticmethod
    def _fake_result(task: Task) -> bytes:
        # результат всегда png-байты, как и от настоящего процессора;
        # фейковый "фильтр" просто возвращает исходную картинку
        try:
            return base64.b64decode(task.payload.get("image") or "", validate=True)
        except (binascii.Error, ValueError):
            return _PNG_1X1
