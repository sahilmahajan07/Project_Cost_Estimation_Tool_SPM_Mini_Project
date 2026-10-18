"""Database connection and initialization helpers."""
import sqlite3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("PCET_DB_PATH", ROOT / "database" / "pcet.db")).resolve()
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        # Lightweight additive migration for databases created by an earlier prototype build.
        change_columns = {row[1] for row in connection.execute("PRAGMA table_info(spm_changes)")}
        if change_columns and "updated_at" not in change_columns:
            connection.execute("ALTER TABLE spm_changes ADD COLUMN updated_at TEXT NOT NULL DEFAULT '1970-01-01 00:00:00'")
        connection.execute(
            "INSERT OR IGNORE INTO users(full_name,email,role) VALUES(?,?,?)",
            ("Demo Project Manager", "pm@example.test", "Project Manager"),
        )
        connection.commit()
