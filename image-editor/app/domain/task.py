import enum
import time


class TaskStatus(str, enum.Enum):
    in_progress = "in_progress"
    ready = "ready"


class Task:
    """Задача пользователя: обработать изображение фильтром"""

    def __init__(
        self,
        task_id: str,
        payload: dict,
        status: TaskStatus = TaskStatus.in_progress,
        result: str | None = None,
        created_at: float | None = None,
    ) -> None:
        self.task_id = task_id
        self.payload = payload
        self.status = status
        self.result = result
        self.created_at = created_at if created_at is not None else time.time()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
        }

    def __repr__(self) -> str:
        return f"<Task {self.task_id} {self.status.value}>"
