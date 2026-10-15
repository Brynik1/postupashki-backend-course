"""Схема таблиц через SQLAlchemy Core: описываем один раз, SQL синхронен"""

from sqlalchemy import MetaData, Table, Column, Uuid, String, Text, LargeBinary, DateTime, func, CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("username", String(64), unique=True, nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

tasks = Table(
    "tasks",
    metadata,
    Column("task_id", Uuid, primary_key=True),
    Column("user_id", Uuid, ForeignKey("users.id"), nullable=False),
    Column("payload", JSONB, nullable=False),
    Column(
        "status",
        Text,
        CheckConstraint("status IN ('in_progress', 'ready', 'failed')", name="ck_tasks_status"),
        nullable=False,
    ),
    Column("result", LargeBinary, nullable=True),
    Column("error", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

Index("idx_tasks_user_id", tasks.c.user_id)
