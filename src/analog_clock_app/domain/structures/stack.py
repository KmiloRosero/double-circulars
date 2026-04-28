from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Optional, TypeVar

from .dynamic_array import DynamicArray


T = TypeVar("T")


@dataclass(slots=True)
class Stack(Generic[T]):
    """A LIFO stack implemented on top of a dynamic array."""

    _items: DynamicArray[T]

    def __init__(self, values: Optional[Iterable[T]] = None) -> None:
        self._items = DynamicArray(values)

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return self._items.is_empty()

    def clear(self) -> None:
        self._items.clear()

    def push(self, value: T) -> None:
        self._items.append(value)

    def pop(self) -> T:
        return self._items.pop()

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("peek from empty Stack")
        return self._items.get(len(self._items) - 1)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

