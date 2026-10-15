import enum
import time


class TaskStatus(str, enum.Enum):
    in_progress = "in_progress"
    ready = "ready"
    failed = "failed"


class Task:
    """Задача пользователя: обработать изображение фильтром"""

    def __init__(
        self,
        task_id: str,
        payload: dict,
        status: TaskStatus = TaskStatus.in_progress,
        user_id: str | None = None,
        result: bytes | None = None,
        error: str | None = None,
        created_at: float | None = None,
    ) -> None:
        self.task_id = task_id
        self.payload = payload
        self.status = status
        self.user_id = user_id  # владелец таски
        self.result = result  # готовая картинка, png-байты
        self.error = error  # причина failed, если обработчик упал
        self.created_at = created_at if created_at is not None else time.time()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
        }

    def __repr__(self) -> str:
        return f"<Task {self.task_id} {self.status.value}>"
