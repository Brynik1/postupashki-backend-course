from app.application.auth_service import AuthService
from app.application.task_service import TaskService
from app.config import Settings
from app.infrastructure.processing.local_runner import LocalImageProcessor
from app.infrastructure.processing.rabbit import RabbitMQTaskExecutor
from app.infrastructure.storage.migrations import run_migrations
from app.infrastructure.storage.postgres import PostgresTaskStorage, PostgresUserStorage
from app.infrastructure.storage.ram import RamSessionStorage, RamTaskStorage, RamUserStorage
from app.infrastructure.storage.redis_sessions import RedisSessionStorage


class Container:
    """Собирает все зависимости приложения вместе"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._pool = None
        if self.settings.database_url:
            from psycopg_pool import ConnectionPool

            run_migrations(self.settings.database_url)
            self._pool = ConnectionPool(self.settings.database_url, open=True, min_size=1, max_size=8)

        self.user_repository = self._user_repository()
        self.session_repository = self._session_repository()
        self.task_repository = self._task_repository()
        self.auth_service = AuthService(self.user_repository, self.session_repository)
        self.task_service = TaskService(
            task_repository=self.task_repository,
            executor=self._executor(),
        )

    def _user_repository(self):
        if self._pool is not None:
            return PostgresUserStorage(self._pool)
        return RamUserStorage()

    def _task_repository(self):
        if self._pool is not None:
            return PostgresTaskStorage(self._pool)
        return RamTaskStorage()

    def _session_repository(self):
        if self.settings.redis_url:
            import redis

            client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
            return RedisSessionStorage(client)
        return RamSessionStorage()

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
