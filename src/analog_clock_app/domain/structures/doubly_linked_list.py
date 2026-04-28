from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class DoublyNode(Generic[T]):
    value: T
    next: Optional["DoublyNode[T]"] = None
    prev: Optional["DoublyNode[T]"] = None


class DoublyLinkedList(Generic[T]):
    """A basic doubly linked list with head/tail and O(1) append/pop."""

    __slots__ = ("_head", "_tail", "_size")

    def __init__(self, values: Optional[Iterable[T]] = None) -> None:
        self._head: Optional[DoublyNode[T]] = None
        self._tail: Optional[DoublyNode[T]] = None
        self._size: int = 0
        if values is not None:
            for v in values:
                self.append(v)

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def clear(self) -> None:
        self._head = None
        self._tail = None
        self._size = 0

    def append(self, value: T) -> None:
        node = DoublyNode(value=value)
        if self._tail is None:
            self._head = node
            self._tail = node
            self._size = 1
            return
        node.prev = self._tail
        self._tail.next = node
        self._tail = node
        self._size += 1

    def pop_left(self) -> T:
        if self._head is None:
            raise IndexError("pop from empty DoublyLinkedList")
        value = self._head.value
        next_node = self._head.next
        self._head.next = None
        if next_node is not None:
            next_node.prev = None
        self._head = next_node
        self._size -= 1
        if self._head is None:
            self._tail = None
        return value

    def pop_right(self) -> T:
        if self._tail is None:
            raise IndexError("pop from empty DoublyLinkedList")
        value = self._tail.value
        prev_node = self._tail.prev
        self._tail.prev = None
        if prev_node is not None:
            prev_node.next = None
        self._tail = prev_node
        self._size -= 1
        if self._tail is None:
            self._head = None
        return value

    def to_list(self) -> list[T]:
        return list(self)

    def __iter__(self) -> Iterator[T]:
        node = self._head
        while node is not None:
            yield node.value
            node = node.next

