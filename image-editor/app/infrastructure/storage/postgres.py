import json

from app.domain.repositories import TaskRepository, UserRepository
from app.domain.task import Task, TaskStatus
from app.domain.user import User


class PostgresTaskStorage(TaskRepository):
    """Задачи в PostgreSQL; запросы вместо словаря, остальное - как в RAM"""

    def __init__(self, pool) -> None:
        self._pool = pool

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

    def save(self, task: Task) -> Task:
        task_id = task.task_id
        payload = json.dumps(task.payload)
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (task_id, user_id, payload, status, result, error)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (task_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    payload = EXCLUDED.payload,
                    status = EXCLUDED.status,
                    result = EXCLUDED.result,
                    error = EXCLUDED.error
                """,
                (task_id, task.user_id, payload, task.status.value, task.result, task.error),
            )
        return self.get(task_id)

    def update(self, task: Task) -> None:
        self.save(task)

    def get(self, task_id: str) -> Task | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT task_id, payload, status, user_id, result, error FROM tasks WHERE task_id = %s",
                (task_id,),
            ).fetchone()
        return self._from_row(row)


class PostgresUserStorage(UserRepository):
    """Пользователи в PostgreSQL (password_hash уже соленый, см. domain)"""

    def __init__(self, pool) -> None:
        self._pool = pool

    def add(self, user: User) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute(
                    "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s)",
                    (user.id, user.username, user.password_hash),
                )
            return True
        except Exception:
            # конфликт unique(username) - имя занято
            return False

    def get_by_username(self, username: str) -> User | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,),
            ).fetchone()
        if row is None:
            return None
        return User(user_id=str(row[0]), username=row[1], password_hash=row[2])
