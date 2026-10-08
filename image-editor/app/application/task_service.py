import base64
import binascii
import uuid

from app.domain.exceptions import (
    InvalidCommitPayload,
    TaskAlreadyReady,
    TaskNotFound,
    TaskNotReady,
)
from app.domain.repositories import TaskRepository
from app.domain.task import Task, TaskStatus
from app.domain.task_executor import TaskExecutor


class TaskResult:
    """Ответ юзкейса get_result без знания HTTP"""

    def __init__(self, status: str, result: str | None) -> None:
        self.status = status
        self.result = result

    def to_dict(self) -> dict:
        out = {"status": self.status}
        if self.result is not None:
            out["result"] = self.result
        return out


class TaskService:
    def __init__(self, task_repository: TaskRepository, executor: TaskExecutor) -> None:
        self._repository = task_repository
        self._executor = executor

    def create_task(self, payload: dict, user_id: str) -> Task:
        """Загрузка таски на обработку; id выдается сразу, результат позже"""
        task = self._repository.save(
            Task(task_id=str(uuid.uuid4()), payload=payload, user_id=user_id)
        )
        self._executor.execute(task)
        return task

    def commit_result(self, task_id: str, image_b64: str) -> Task:
        """Обработчик готов и вернул результат (через /commit)"""
        try:
            image = base64.b64decode(image_b64, validate=True)
        except (binascii.Error, ValueError):
            # невалидный base64 - таску не трогаем
            raise InvalidCommitPayload()
        task = self._get_or_404(task_id)
        if task.status is TaskStatus.ready:
            raise TaskAlreadyReady()
        task.status = TaskStatus.ready
        task.result = image
        return self._repository.save(task)

    def commit_failure(self, task_id: str, reason: str) -> Task:
        """Обработчик не смог обработать таску - переводим ее в failed"""
        task = self._get_or_404(task_id)
        if task.status is TaskStatus.ready:
            raise TaskAlreadyReady()
        task.status = TaskStatus.failed
        task.error = reason
        return self._repository.save(task)

    def get_status(self, task_id: str, user_id: str) -> dict:
        task = self._get_owned_or_404(task_id, user_id)
        return {"status": task.status.value}

    def get_result(self, task_id: str, user_id: str) -> TaskResult:
        task = self._get_owned_or_404(task_id, user_id)
        ready = task.status is TaskStatus.ready
        return TaskResult(
            status=task.status.value,
            # картинка отдается base64, чтобы отобразить в браузере (readme hw3)
            result=base64.b64encode(task.result).decode("ascii") if ready and task.result else None,
        )

    def get_image(self, task_id: str, user_id: str) -> tuple[bytes, str]:
        """Сырые png-байты для отдачи картинки в браузере"""
        task = self._get_owned_or_404(task_id, user_id)
        if task.status is not TaskStatus.ready:
            raise TaskNotReady()
        return task.result or b"", "png"

    def _get_or_404(self, task_id: str) -> Task:
        try:
            uuid.UUID(task_id)
        except (ValueError, AttributeError):
            # не-uuid, пришедший в пути/вебхуке, не должен долбить SQL
            raise TaskNotFound()
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFound()
        return task

    def _get_owned_or_404(self, task_id: str, user_id: str) -> Task:
        task = self._get_or_404(task_id)
        if task.user_id != user_id:
            # чужую таску маскируем под несуществующую, чтобы не палить id
            raise TaskNotFound()
        return task
