from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from analog_clock_app.config.settings import AppSettings

from .db import Database
from .schema import init_schema


class SettingsRepository(Protocol):
    """Persistence boundary for settings."""

    def get_settings(self) -> AppSettings: ...

    def save_settings(self, settings: AppSettings) -> None: ...


@dataclass(frozen=True, slots=True)
class Preset:
    """A persisted snapshot of settings."""

    id: str
    name: str
    created_at_utc: datetime
    settings: AppSettings


class PresetRepository(Protocol):
    def list_presets(self) -> list[Preset]: ...

    def get_preset(self, preset_id: str) -> Preset: ...

    def save_preset(self, name: str, settings: AppSettings) -> Preset: ...

    def delete_preset(self, preset_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class Alarm:
    id: str
    label: str
    hour: int
    minute: int
    enabled: bool
    timezone: str
    last_triggered_local_date: str | None


class AlarmRepository(Protocol):
    def list_alarms(self) -> list[Alarm]: ...

    def add_alarm(self, label: str, hour: int, minute: int, timezone: str) -> Alarm: ...

    def set_enabled(self, alarm_id: str, enabled: bool) -> None: ...

    def delete_alarm(self, alarm_id: str) -> None: ...

    def mark_triggered(self, alarm_id: str, local_date: str) -> None: ...


@dataclass(frozen=True, slots=True)
class WorldClockFavorite:
    id: str
    label: str
    timezone: str


class WorldClockRepository(Protocol):
    def list_favorites(self) -> list[WorldClockFavorite]: ...

    def add_favorite(self, label: str, timezone: str) -> WorldClockFavorite: ...

    def delete_favorite(self, favorite_id: str) -> None: ...


class SQLiteSettingsRepository(SettingsRepository):
    """SQLite-backed settings repository."""

    def __init__(self, db: Database) -> None:
        self._db = db
        with self._db.session() as conn:
            init_schema(conn)

    def get_settings(self) -> AppSettings:
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
            if row is None:
                init_schema(conn)
                row = conn.execute("SELECT * FROM app_settings WHERE id = 1").fetchone()
            assert row is not None
            try:
                timezone = row["timezone"]
            except Exception:
                timezone = "America/Bogota"

            try:
                dark_theme = bool(row["dark_theme"])
            except Exception:
                dark_theme = False
            return AppSettings(
                timezone=timezone,
                dark_theme=dark_theme,
                time_mode=row["time_mode"],
                simulation_speed=float(row["simulation_speed"]),
                time_offset_seconds=int(row["time_offset_seconds"]),
                face_color=row["face_color"],
                tick_color=row["tick_color"],
                hand_color=row["hand_color"],
                show_major_ticks_only=bool(row["show_major_ticks_only"]),
                enable_shadow_layer=bool(row["enable_shadow_layer"]),
                enable_center_dot_layer=bool(row["enable_center_dot_layer"]),
            )

    def save_settings(self, settings: AppSettings) -> None:
        data = asdict(settings)
        with self._db.session() as conn:
            conn.execute(
                """
                UPDATE app_settings
                SET timezone = :timezone,
                    dark_theme = :dark_theme,
                    time_mode = :time_mode,
                    simulation_speed = :simulation_speed,
                    time_offset_seconds = :time_offset_seconds,
                    face_color = :face_color,
                    tick_color = :tick_color,
                    hand_color = :hand_color,
                    show_major_ticks_only = :show_major_ticks_only,
                    enable_shadow_layer = :enable_shadow_layer,
                    enable_center_dot_layer = :enable_center_dot_layer
                WHERE id = 1
                """,
                {
                    **data,
                    "dark_theme": 1 if settings.dark_theme else 0,
                    "show_major_ticks_only": 1 if settings.show_major_ticks_only else 0,
                    "enable_shadow_layer": 1 if settings.enable_shadow_layer else 0,
                    "enable_center_dot_layer": 1 if settings.enable_center_dot_layer else 0,
                },
            )
            conn.commit()


class CachedSettingsRepositoryProxy(SettingsRepository):
    """Proxy that caches settings reads and forwards writes to the inner repo."""

    def __init__(self, inner: SettingsRepository) -> None:
        self._inner = inner
        self._cached: AppSettings | None = None

    def get_settings(self) -> AppSettings:
        if self._cached is None:
            self._cached = self._inner.get_settings()
        return self._cached

    def save_settings(self, settings: AppSettings) -> None:
        self._inner.save_settings(settings)
        self._cached = settings


class SQLitePresetRepository(PresetRepository):
    """SQLite-backed repository for saved presets."""

    def __init__(self, db: Database) -> None:
        self._db = db
        with self._db.session() as conn:
            init_schema(conn)

    def list_presets(self) -> list[Preset]:
        with self._db.session() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at_utc, settings_json FROM presets ORDER BY created_at_utc DESC"
            ).fetchall()
            return [self._row_to_preset(r) for r in rows]

    def get_preset(self, preset_id: str) -> Preset:
        with self._db.session() as conn:
            row = conn.execute(
                "SELECT id, name, created_at_utc, settings_json FROM presets WHERE id = ?",
                (preset_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Preset not found: {preset_id}")
            return self._row_to_preset(row)

    def save_preset(self, name: str, settings: AppSettings) -> Preset:
        preset_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        payload = json.dumps(asdict(settings), separators=(",", ":"), ensure_ascii=False)

        with self._db.session() as conn:
            conn.execute(
                "INSERT INTO presets (id, name, created_at_utc, settings_json) VALUES (?, ?, ?, ?)",
                (preset_id, name, created_at.isoformat(), payload),
            )
            conn.commit()
        return Preset(id=preset_id, name=name, created_at_utc=created_at, settings=settings)

    def delete_preset(self, preset_id: str) -> None:
        with self._db.session() as conn:
            conn.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
            conn.commit()

    def _row_to_preset(self, row) -> Preset:
        created_at = datetime.fromisoformat(row["created_at_utc"])
        data = json.loads(row["settings_json"])
        settings = AppSettings(**data)
        return Preset(
            id=row["id"],
            name=row["name"],
            created_at_utc=created_at,
            settings=settings,
        )


class SQLiteAlarmRepository(AlarmRepository):
    def __init__(self, db: Database) -> None:
        self._db = db
        with self._db.session() as conn:
            init_schema(conn)

    def list_alarms(self) -> list[Alarm]:
        with self._db.session() as conn:
            rows = conn.execute(
                "SELECT id, label, hour, minute, enabled, timezone, last_triggered_local_date FROM alarms ORDER BY hour, minute"
            ).fetchall()
            return [
                Alarm(
                    id=r["id"],
                    label=r["label"],
                    hour=int(r["hour"]),
                    minute=int(r["minute"]),
                    enabled=bool(r["enabled"]),
                    timezone=r["timezone"],
                    last_triggered_local_date=r["last_triggered_local_date"],
                )
                for r in rows
            ]

    def add_alarm(self, label: str, hour: int, minute: int, timezone: str) -> Alarm:
        alarm_id = str(uuid4())
        with self._db.session() as conn:
            conn.execute(
                "INSERT INTO alarms (id, label, hour, minute, enabled, timezone, last_triggered_local_date) VALUES (?, ?, ?, ?, 1, ?, NULL)",
                (alarm_id, label, int(hour), int(minute), timezone),
            )
            conn.commit()
        return Alarm(
            id=alarm_id,
            label=label,
            hour=int(hour),
            minute=int(minute),
            enabled=True,
            timezone=timezone,
            last_triggered_local_date=None,
        )

    def set_enabled(self, alarm_id: str, enabled: bool) -> None:
        with self._db.session() as conn:
            conn.execute("UPDATE alarms SET enabled = ? WHERE id = ?", (1 if enabled else 0, alarm_id))
            conn.commit()

    def delete_alarm(self, alarm_id: str) -> None:
        with self._db.session() as conn:
            conn.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
            conn.commit()

    def mark_triggered(self, alarm_id: str, local_date: str) -> None:
        with self._db.session() as conn:
            conn.execute(
                "UPDATE alarms SET last_triggered_local_date = ? WHERE id = ?",
                (local_date, alarm_id),
            )
            conn.commit()


class SQLiteWorldClockRepository(WorldClockRepository):
    def __init__(self, db: Database) -> None:
        self._db = db
        with self._db.session() as conn:
            init_schema(conn)

    def list_favorites(self) -> list[WorldClockFavorite]:
        with self._db.session() as conn:
            rows = conn.execute(
                "SELECT id, label, timezone FROM world_clock_favorites ORDER BY label"
            ).fetchall()
            return [WorldClockFavorite(id=r["id"], label=r["label"], timezone=r["timezone"]) for r in rows]

    def add_favorite(self, label: str, timezone: str) -> WorldClockFavorite:
        fav_id = str(uuid4())
        with self._db.session() as conn:
            conn.execute(
                "INSERT INTO world_clock_favorites (id, label, timezone) VALUES (?, ?, ?)",
                (fav_id, label, timezone),
            )
            conn.commit()
        return WorldClockFavorite(id=fav_id, label=label, timezone=timezone)

    def delete_favorite(self, favorite_id: str) -> None:
        with self._db.session() as conn:
            conn.execute("DELETE FROM world_clock_favorites WHERE id = ?", (favorite_id,))
            conn.commit()

