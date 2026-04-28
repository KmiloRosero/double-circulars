import os
import tempfile

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import (
    CachedSettingsRepositoryProxy,
    SQLitePresetRepository,
    SQLiteSettingsRepository,
)
from analog_clock_app.services.preset_service import PresetService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService


def test_settings_persist_between_instances() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "app.db")
        db = Database(db_path)

        repo1 = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
        service1 = SettingsService(repo1)
        service1.apply_patch(
            SettingsPatch(
                time_mode="simulated",
                simulation_speed=2.5,
                time_offset_seconds=10,
                background_mode="black",
            )
        )

        repo2 = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
        service2 = SettingsService(repo2)
        loaded = service2.get()
        assert loaded.time_mode == "simulated"
        assert loaded.simulation_speed == 2.5
        assert loaded.time_offset_seconds == 10
        assert loaded.background_mode == "black"


def test_presets_persist_and_apply() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "app.db")
        db = Database(db_path)

        settings_repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
        presets_repo = SQLitePresetRepository(db)
        preset_service = PresetService(presets=presets_repo, settings=settings_repo)
        settings_service = SettingsService(settings_repo)

        settings_service.save(AppSettings(time_mode="simulated", simulation_speed=4.0, hand_color="#00ff00"))
        created = preset_service.save_current_settings_as_preset("Fast Green")

        settings_service.save(AppSettings(time_mode="real"))
        applied = preset_service.apply_preset(created.id)
        assert applied.time_mode == "simulated"
        assert applied.simulation_speed == 4.0
        assert applied.hand_color == "#00ff00"

        presets_repo2 = SQLitePresetRepository(db)
        all_presets = presets_repo2.list_presets()
        assert len(all_presets) == 1
        assert all_presets[0].name == "Fast Green"
