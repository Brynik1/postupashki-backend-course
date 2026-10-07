import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Настройки сервиса; вся конфигурация живет здесь и через env"""

    work_min_seconds: float = 2.0
    work_max_seconds: float = 5.0
    executor_workers: int = 8
    host: str = "0.0.0.0"
    port: int = 8000
    # пусто = работать без брокера, в тех же потоках (для локальной разработки)
    rabbit_url: str = ""
    task_queue: str = "processing_tasks"
    # общий секрет api <-> processor для вебхука /commit
    commit_secret: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            work_min_seconds=float(os.getenv("WORK_MIN_SECONDS", "2.0")),
            work_max_seconds=float(os.getenv("WORK_MAX_SECONDS", "5.0")),
            executor_workers=int(os.getenv("EXECUTOR_WORKERS", "8")),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            rabbit_url=os.getenv("RABBIT_URL", ""),
            task_queue=os.getenv("TASK_QUEUE", "processing_tasks"),
            commit_secret=os.getenv("COMMIT_SECRET", ""),
        )
