from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import DATABASE_PATH


class Database:
    def __init__(self, path: str = DATABASE_PATH) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                logs_channel_id INTEGER,
                ticket_category_id INTEGER,
                autorole_id INTEGER,
                suggestions_channel_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                message_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def _ensure_guild(self, guild_id: int) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,)
        )
        self.connection.commit()

    def get_settings(self, guild_id: int) -> sqlite3.Row:
        self._ensure_guild(guild_id)
        return self.connection.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()

    def set_setting(self, guild_id: int, key: str, value: int | None) -> None:
        allowed = {
            "welcome_channel_id",
            "logs_channel_id",
            "ticket_category_id",
            "autorole_id",
            "suggestions_channel_id",
        }
        if key not in allowed:
            raise ValueError(f"Unknown guild setting: {key}")
        self._ensure_guild(guild_id)
        self.connection.execute(
            f"UPDATE guild_settings SET {key} = ? WHERE guild_id = ?",
            (value, guild_id),
        )
        self.connection.commit()

    def add_warning(
        self, guild_id: int, user_id: int, moderator_id: int, reason: str
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                user_id,
                moderator_id,
                reason,
                datetime.now(UTC).isoformat(),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_warnings(self, guild_id: int, user_id: int) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                """
                SELECT * FROM warnings
                WHERE guild_id = ? AND user_id = ?
                ORDER BY id DESC
                """,
                (guild_id, user_id),
            )
        )

    def clear_warnings(self, guild_id: int, user_id: int) -> int:
        cursor = self.connection.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        self.connection.commit()
        return cursor.rowcount

    def add_suggestion(
        self, guild_id: int, user_id: int, content: str, message_id: int | None = None
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO suggestions (guild_id, user_id, content, message_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                user_id,
                content,
                message_id,
                datetime.now(UTC).isoformat(),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def set_suggestion_message(self, suggestion_id: int, message_id: int) -> None:
        self.connection.execute(
            "UPDATE suggestions SET message_id = ? WHERE id = ?",
            (message_id, suggestion_id),
        )
        self.connection.commit()

    def update_suggestion_status(self, suggestion_id: int, status: str) -> None:
        self.connection.execute(
            "UPDATE suggestions SET status = ? WHERE id = ?",
            (status, suggestion_id),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()