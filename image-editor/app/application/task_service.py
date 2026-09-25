import uuid

from app.domain.exceptions import TaskNotFound
from app.domain.repositories import TaskRepository
from app.domain.task import Task, TaskStatus
from app.infrastructure.processing.local_runner import TaskExecutor


class TaskService:
    def __init__(self, task_repository: TaskRepository, executor: TaskExecutor) -> None:
        self._repository = task_repository
        self._executor = executor

    def create_task(self, payload: dict) -> Task:
        """Загрузка таски на обработку; id выдается сразу, результат позже"""
        task = self._repository.save(
            Task(task_id=str(uuid.uuid4()), payload=payload)
        )
        self._executor.execute(task)
        return task

    def get_status(self, task_id: str) -> dict:
        task = self._get_or_404(task_id)
        return {"status": task.status.value}

    def get_result(self, task_id: str) -> dict:
        task = self._get_or_404(task_id)
        if task.status is not TaskStatus.ready:
            return {"status": task.status.value}
        return {"status": task.status.value, "result": task.result}

    def _get_or_404(self, task_id: str) -> Task:
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFound()
        return task
