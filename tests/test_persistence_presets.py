import os
import tempfile
import unittest

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.persistence.db import Database
from analog_clock_app.persistence.repositories import (
    CachedSettingsRepositoryProxy,
    SQLitePresetRepository,
    SQLiteSettingsRepository,
)
from analog_clock_app.services.preset_service import PresetService
from analog_clock_app.services.settings_service import SettingsPatch, SettingsService


class TestPersistenceSettingsAndPresets(unittest.TestCase):
    def test_settings_persist_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "app.db")
            db = Database(db_path)

            repo1 = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
            service1 = SettingsService(repo1)
            updated = service1.apply_patch(
                SettingsPatch(time_mode="simulated", simulation_speed=2.5, time_offset_seconds=120)
            )
            self.assertEqual(updated.time_mode, "simulated")

            repo2 = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
            service2 = SettingsService(repo2)
            loaded = service2.get()
            self.assertEqual(loaded.time_mode, "simulated")
            self.assertEqual(loaded.simulation_speed, 2.5)
            self.assertEqual(loaded.time_offset_seconds, 120)

    def test_presets_persist_and_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "app.db")
            db = Database(db_path)

            settings_repo = CachedSettingsRepositoryProxy(SQLiteSettingsRepository(db))
            presets_repo = SQLitePresetRepository(db)
            settings_service = SettingsService(settings_repo)
            preset_service = PresetService(presets=presets_repo, settings=settings_repo)

            settings_service.save(
                AppSettings(
                    time_mode="simulated",
                    simulation_speed=4.0,
                    time_offset_seconds=30,
                    face_color="#000000",
                    tick_color="#ffffff",
                    hand_color="#00ff00",
                    show_major_ticks_only=True,
                    enable_shadow_layer=False,
                    enable_center_dot_layer=True,
                )
            )

            created = preset_service.save_current_settings_as_preset("Fast Green")
            self.assertEqual(created.name, "Fast Green")

            settings_service.save(AppSettings(time_mode="real"))
            applied = preset_service.apply_preset(created.id)
            self.assertEqual(applied.time_mode, "simulated")
            self.assertEqual(applied.simulation_speed, 4.0)
            self.assertEqual(applied.hand_color, "#00ff00")

            presets_repo2 = SQLitePresetRepository(db)
            all_presets = presets_repo2.list_presets()
            self.assertEqual(len(all_presets), 1)
            self.assertEqual(all_presets[0].name, "Fast Green")


if __name__ == "__main__":
    unittest.main()

