from __future__ import annotations

from dataclasses import dataclass

from analog_clock_app.config.settings import AppSettings
from analog_clock_app.domain.structures.queue import Queue
from analog_clock_app.domain.structures.stack import Stack


@dataclass(slots=True)
class HistoryService:
    """In-memory history for undo/redo and an event stream for the UI."""

    _undo: Stack[AppSettings]
    _redo: Stack[AppSettings]
    _events: Queue[str]
    _max_events: int

    def __init__(self, max_events: int = 25) -> None:
        self._undo = Stack()
        self._redo = Stack()
        self._events = Queue()
        self._max_events = max_events

    def record_change(self, before: AppSettings, after: AppSettings, label: str) -> None:
        self._undo.push(before)
        self._redo.clear()
        self._log(label)

    def can_undo(self) -> bool:
        return not self._undo.is_empty()

    def can_redo(self) -> bool:
        return not self._redo.is_empty()

    def undo(self, current: AppSettings) -> AppSettings:
        if not self.can_undo():
            raise IndexError("Nothing to undo")
        previous = self._undo.pop()
        self._redo.push(current)
        self._log("Se deshizo el último cambio")
        return previous

    def redo(self, current: AppSettings) -> AppSettings:
        if not self.can_redo():
            raise IndexError("Nothing to redo")
        next_settings = self._redo.pop()
        self._undo.push(current)
        self._log("Se rehizo el último cambio")
        return next_settings

    def events(self) -> list[str]:
        return self._events.to_list()

    def _log(self, message: str) -> None:
        self._events.enqueue(message)
        while len(self._events) > self._max_events:
            self._events.dequeue()

