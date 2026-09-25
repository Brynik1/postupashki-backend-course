from app.application.task_service import TaskService
from app.config import Settings
from app.infrastructure.processing.local_runner import LocalImageProcessor
from app.infrastructure.storage.ram import RamTaskStorage


class Container:
    """Собирает все зависимости приложения вместе"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.task_repository = RamTaskStorage()
        self.task_service = TaskService(
            task_repository=self.task_repository,
            executor=LocalImageProcessor(
                self.task_repository,
                min_work_seconds=self.settings.work_min_seconds,
                max_work_seconds=self.settings.work_max_seconds,
                workers=self.settings.executor_workers,
            ),
        )
