"""Хранилища поверх SQLAlchemy: все запросы идут как bound-параметры,
вручную SQL-строки не склеиваем - инъекции исключены"""

import json
import uuid

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.repositories import TaskRepository, UserRepository
from app.domain.task import Task, TaskStatus
from app.domain.user import User
from app.infrastructure.storage.tables import tasks, users


class PostgresTaskStorage(TaskRepository):
    """Задачи в PostgreSQL; тот же контракт save/update/get, что и в RAM"""

    def __init__(self, engine) -> None:
        self._engine = engine

    @staticmethod
    def _from_row(row) -> Task | None:
        if row is None:
            return None
        task_id, payload, status, user_id, result, error = row
        return Task(
            task_id=str(task_id),
            payload=payload,
            status=TaskStatus(status),
            user_id=str(user_id),
            result=bytes(result) if result is not None else None,
            error=error,
        )

    @staticmethod
    def _values(task: Task) -> dict:
        return {
            "task_id": uuid.UUID(task.task_id),
            "user_id": uuid.UUID(task.user_id),
            "payload": task.payload,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
        }

    def save(self, task: Task) -> Task:
        # upsert: новый таск вставляем, существующий - обновляем поля целиком
        stmt = pg_insert(tasks).values(**self._values(task))
        stmt = stmt.on_conflict_do_update(
            index_elements=[tasks.c.task_id],
            set_={
                "user_id": stmt.excluded.user_id,
                "payload": stmt.excluded.payload,
                "status": stmt.excluded.status,
                "result": stmt.excluded.result,
                "error": stmt.excluded.error,
            },
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
        return self.get(task.task_id)

    def update(self, task: Task) -> None:
        self.save(task)

    def get(self, task_id: str) -> Task | None:
        stmt = select(
            tasks.c.task_id, tasks.c.payload, tasks.c.status,
            tasks.c.user_id, tasks.c.result, tasks.c.error,
        ).where(tasks.c.task_id == uuid.UUID(task_id))
        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        return self._from_row(row)


class PostgresUserStorage(UserRepository):
    """Пользователи в PostgreSQL (password_hash уже соленый, см. domain)"""

    def __init__(self, engine) -> None:
        self._engine = engine

    def add(self, user: User) -> bool:
        try:
            with self._engine.begin() as conn:
                conn.execute(
                    insert(users).values(
                        id=uuid.UUID(user.id),
                        username=user.username,
                        password_hash=user.password_hash,
                    )
                )
            return True
        except IntegrityError:
            # конфликт unique(username) - имя занято
            return False

    def get_by_username(self, username: str) -> User | None:
        stmt = select(users.c.id, users.c.username, users.c.password_hash).where(
            users.c.username == username
        )
        with self._engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        if row is None:
            return None
        return User(user_id=str(row[0]), username=row[1], password_hash=row[2])
