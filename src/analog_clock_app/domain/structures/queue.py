from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class Queue(Generic[T]):
    """A FIFO queue implemented as a circular buffer.

    Operations are amortized O(1). Capacity grows automatically.
    """

    _buffer: list[Optional[T]]
    _head: int
    _tail: int
    _size: int

    def __init__(self, values: Optional[Iterable[T]] = None) -> None:
        self._buffer = [None] * 8
        self._head = 0
        self._tail = 0
        self._size = 0
        if values is not None:
            for v in values:
                self.enqueue(v)

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def clear(self) -> None:
        self._buffer = [None] * 8
        self._head = 0
        self._tail = 0
        self._size = 0

    def enqueue(self, value: T) -> None:
        if self._size == len(self._buffer):
            self._grow()
        self._buffer[self._tail] = value
        self._tail = (self._tail + 1) % len(self._buffer)
        self._size += 1

    def dequeue(self) -> T:
        if self._size == 0:
            raise IndexError("dequeue from empty Queue")
        value = self._buffer[self._head]
        self._buffer[self._head] = None
        self._head = (self._head + 1) % len(self._buffer)
        self._size -= 1
        return value  # type: ignore[return-value]

    def peek(self) -> T:
        if self._size == 0:
            raise IndexError("peek from empty Queue")
        value = self._buffer[self._head]
        return value  # type: ignore[return-value]

    def to_list(self) -> list[T]:
        out: list[T] = []
        idx = self._head
        for _ in range(self._size):
            out.append(self._buffer[idx])  # type: ignore[arg-type]
            idx = (idx + 1) % len(self._buffer)
        return out

    def __iter__(self) -> Iterator[T]:
        return iter(self.to_list())

    def _grow(self) -> None:
        new_capacity = max(2 * len(self._buffer), 8)
        new_buffer: list[Optional[T]] = [None] * new_capacity
        idx = self._head
        for i in range(self._size):
            new_buffer[i] = self._buffer[idx]
            idx = (idx + 1) % len(self._buffer)
        self._buffer = new_buffer
        self._head = 0
        self._tail = self._size

