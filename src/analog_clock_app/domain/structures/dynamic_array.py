from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class DynamicArray(Generic[T]):
    """A thin wrapper around Python's list to expose an explicit dynamic array API.

    This is mainly educational for demonstrating the array-based approach alongside
    linked structures.
    """

    _data: list[T]

    def __init__(self, values: Optional[Iterable[T]] = None) -> None:
        self._data = list(values) if values is not None else []

    def __len__(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def clear(self) -> None:
        self._data.clear()

    def append(self, value: T) -> None:
        self._data.append(value)

    def pop(self) -> T:
        if not self._data:
            raise IndexError("pop from empty DynamicArray")
        return self._data.pop()

    def get(self, index: int) -> T:
        return self._data[index]

    def set(self, index: int, value: T) -> None:
        self._data[index] = value

    def to_list(self) -> list[T]:
        return list(self._data)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

