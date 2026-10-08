"""Простейший раннер SQL-миграций поверх SQLAlchemy-движка"""

import os

from sqlalchemy import create_engine, text


def run_migrations(database_url: str) -> None:
    migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
    files = sorted(f for f in os.listdir(migrations_dir) if f.endswith(".sql"))
    if not files:
        return

    engine = create_engine(database_url.replace('postgresql://', 'postgresql+psycopg://', 1))
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
            )
            applied = {row[0] for row in conn.execute(text("SELECT version FROM schema_migrations"))}
            for name in files:
                if name in applied:
                    continue
                sql = open(os.path.join(migrations_dir, name), encoding="utf-8").read()
                conn.execute(text(sql))
                conn.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                    {"version": name},
                )
                print(f"migration applied: {name}")
    finally:
        engine.dispose()
