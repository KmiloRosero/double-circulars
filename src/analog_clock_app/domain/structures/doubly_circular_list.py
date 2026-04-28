from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Optional, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class Node(Generic[T]):
    """A node in a doubly circular linked list.

    Each node points to both the next and previous nodes. In a circular list,
    the last node's `next` points to the head and the head's `prev` points
    to the last node.
    """

    value: T
    next: Node[T]
    prev: Node[T]

    @staticmethod
    def singleton(value: T) -> Node[T]:
        """Create a single-node circular list where next/prev point to itself."""

        node: Node[T] = Node.__new__(Node)
        node.value = value
        node.next = node
        node.prev = node
        return node


class DoublyCircularLinkedList(Generic[T]):
    """A doubly circular linked list with a movable current pointer.

    This implementation is designed for scenarios like a clock ring of 60 ticks.
    The list maintains:
    - `head`: a stable entry point
    - `current`: a pointer used for traversal and insert/remove operations
    - `size`: number of nodes
    """

    __slots__ = ("_head", "_current", "_size")

    def __init__(self, values: Optional[Iterable[T]] = None) -> None:
        self._head: Optional[Node[T]] = None
        self._current: Optional[Node[T]] = None
        self._size: int = 0

        if values is not None:
            for value in values:
                if self._size == 0:
                    self.insert_after_current(value)
                else:
                    self.insert_after_current(value)
                    self.move_forward(1)
            if self._head is not None:
                self._current = self._head

    @property
    def size(self) -> int:
        """Number of nodes in the list."""

        return self._size

    @property
    def head(self) -> Optional[Node[T]]:
        """Head node of the list (or None if empty)."""

        return self._head

    @property
    def current(self) -> Optional[Node[T]]:
        """Current node used for traversal and modifications (or None if empty)."""

        return self._current

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def insert_after_current(self, value: T) -> Node[T]:
        """Insert a new node immediately after `current`.

        If the list is empty, the new node becomes both `head` and `current`.

        Returns:
            The inserted node.
        """

        if self._size == 0:
            node = Node.singleton(value)
            self._head = node
            self._current = node
            self._size = 1
            return node

        assert self._current is not None
        current = self._current
        nxt = current.next

        node = Node(value=value, next=nxt, prev=current)
        current.next = node
        nxt.prev = node

        self._size += 1
        return node

    def remove_current(self) -> T:
        """Remove the current node and advance current to the next node.

        Returns:
            The removed node's value.

        Raises:
            IndexError: If the list is empty.
        """

        if self._size == 0:
            raise IndexError("Cannot remove from an empty list")

        assert self._current is not None
        node = self._current
        value = node.value

        if self._size == 1:
            self._head = None
            self._current = None
            self._size = 0
            return value

        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

        if self._head is node:
            self._head = next_node

        self._current = next_node
        self._size -= 1
        return value

    def move_forward(self, n: int) -> Node[T]:
        """Move the current pointer forward by n steps.

        Negative values move backward.

        Returns:
            The new current node.

        Raises:
            IndexError: If the list is empty.
        """

        if self._size == 0:
            raise IndexError("Cannot move in an empty list")
        if n < 0:
            return self.move_backward(-n)

        assert self._current is not None
        steps = n % self._size
        node = self._current
        for _ in range(steps):
            node = node.next
        self._current = node
        return node

    def move_backward(self, n: int) -> Node[T]:
        """Move the current pointer backward by n steps.

        Negative values move forward.

        Returns:
            The new current node.

        Raises:
            IndexError: If the list is empty.
        """

        if self._size == 0:
            raise IndexError("Cannot move in an empty list")
        if n < 0:
            return self.move_forward(-n)

        assert self._current is not None
        steps = n % self._size
        node = self._current
        for _ in range(steps):
            node = node.prev
        self._current = node
        return node

    def to_list(self, limit: Optional[int] = None) -> list[T]:
        """Return list content starting at head, bounded by an optional limit.

        Args:
            limit: Maximum number of elements to return. If None, returns all.

        Notes:
            The limit exists to prevent accidental infinite traversal if this
            structure is used incorrectly.
        """

        if self._size == 0 or self._head is None:
            return []

        if limit is None:
            limit = self._size
        if limit < 0:
            raise ValueError("limit must be non-negative")

        out: list[T] = []
        node = self._head
        for _ in range(min(limit, self._size)):
            out.append(node.value)
            node = node.next
        return out

