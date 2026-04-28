from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.persistence.repositories import WorldClockFavorite, WorldClockRepository


@dataclass(slots=True)
class WorldClockService:
    """Service layer for managing world clock favorites."""

    repo: WorldClockRepository

    def list_favorites(self) -> list[WorldClockFavorite]:
        return self.repo.list_favorites()

    def add_favorite(self, label: str, timezone: str) -> WorldClockFavorite:
        return self.repo.add_favorite(label=label, timezone=timezone)

    def delete_favorite(self, favorite_id: str) -> None:
        self.repo.delete_favorite(favorite_id)

