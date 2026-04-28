from __future__ import annotations

import sqlite3


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        )
        """
    )
    row = conn.execute("SELECT COUNT(*) AS c FROM schema_version").fetchone()
    if row is None or int(row["c"]) == 0:
        conn.execute("INSERT INTO schema_version (version) VALUES (0)")


def _get_schema_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    if row is None:
        return 0
    return int(row["version"])


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("UPDATE schema_version SET version = ?", (version,))


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _migration_1(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            time_mode TEXT NOT NULL,
            simulation_speed REAL NOT NULL,
            time_offset_seconds INTEGER NOT NULL,
            face_color TEXT NOT NULL,
            tick_color TEXT NOT NULL,
            hand_color TEXT NOT NULL,
            show_major_ticks_only INTEGER NOT NULL,
            enable_shadow_layer INTEGER NOT NULL,
            enable_center_dot_layer INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO app_settings (
            id, time_mode, simulation_speed, time_offset_seconds,
            face_color, tick_color, hand_color,
            show_major_ticks_only, enable_shadow_layer, enable_center_dot_layer
        )
        VALUES (1, 'real', 1.0, 0, '#111827', '#E5E7EB', '#F9FAFB', 0, 1, 1)
        ON CONFLICT(id) DO NOTHING
        """
    )


def _migration_2(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS presets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            settings_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_presets_created_at ON presets(created_at_utc)
        """
    )


def _migration_3(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "app_settings", "timezone"):
        conn.execute("ALTER TABLE app_settings ADD COLUMN timezone TEXT NOT NULL DEFAULT 'America/Bogota'")


def _migration_4(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alarms (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            hour INTEGER NOT NULL,
            minute INTEGER NOT NULL,
            enabled INTEGER NOT NULL,
            timezone TEXT NOT NULL,
            last_triggered_local_date TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_alarms_enabled ON alarms(enabled)")


def _migration_5(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS world_clock_favorites (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            timezone TEXT NOT NULL
        )
        """
    )


def _migration_6(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "app_settings", "dark_theme"):
        conn.execute("ALTER TABLE app_settings ADD COLUMN dark_theme INTEGER NOT NULL DEFAULT 0")


def init_schema(conn: sqlite3.Connection) -> None:
    _ensure_schema_version_table(conn)
    current = _get_schema_version(conn)
    migrations = [
        (1, _migration_1),
        (2, _migration_2),
        (3, _migration_3),
        (4, _migration_4),
        (5, _migration_5),
        (6, _migration_6),
    ]
    for version, migrate in migrations:
        if current < version:
            migrate(conn)
            _set_schema_version(conn, version)
            current = version
    conn.commit()

