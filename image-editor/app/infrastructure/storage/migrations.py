"""Простейший раннер SQL-миграций"""

import os

import psycopg


def run_migrations(database_url: str) -> None:
    migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
    files = sorted(f for f in os.listdir(migrations_dir) if f.endswith(".sql"))
    if not files:
        return

    with psycopg.connect(database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
        for name in files:
            if name in applied:
                continue
            sql = open(os.path.join(migrations_dir, name), encoding="utf-8").read()
            conn.execute(sql)
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (name,))
            print(f"migration applied: {name}")
        conn.commit()
