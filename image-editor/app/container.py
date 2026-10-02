from app.application.auth_service import AuthService
from app.application.task_service import TaskService
from app.config import Settings
from app.infrastructure.processing.local_runner import LocalImageProcessor
from app.infrastructure.processing.rabbit import RabbitMQTaskExecutor
from app.infrastructure.storage.ram import RamSessionStorage, RamTaskStorage, RamUserStorage


class Container:
    """Собирает все зависимости приложения вместе"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.user_repository = RamUserStorage()
        self.session_repository = RamSessionStorage()
        self.task_repository = RamTaskStorage()
        self.auth_service = AuthService(self.user_repository, self.session_repository)
        self.task_service = TaskService(
            task_repository=self.task_repository,
            executor=self._executor(),
        )

    def _executor(self):
        # с брокером - ImageProcessor отдельный микросервис,
        # без - фейковый локальный поток для локальной разработки
        if self.settings.rabbit_url:
            return RabbitMQTaskExecutor(self.settings)
        return LocalImageProcessor(
            self.task_repository,
            min_work_seconds=self.settings.work_min_seconds,
            max_work_seconds=self.settings.work_max_seconds,
            workers=self.settings.executor_workers,
        )
