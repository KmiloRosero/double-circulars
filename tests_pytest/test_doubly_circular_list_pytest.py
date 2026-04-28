import pytest

from analog_clock_app.domain.structures.doubly_circular_list import DoublyCircularLinkedList


def test_empty_list() -> None:
    dll: DoublyCircularLinkedList[int] = DoublyCircularLinkedList()
    assert dll.size == 0
    assert dll.is_empty()
    assert dll.to_list() == []

    with pytest.raises(IndexError):
        dll.move_forward(1)
    with pytest.raises(IndexError):
        dll.remove_current()


def test_insert_move_remove() -> None:
    dll: DoublyCircularLinkedList[int] = DoublyCircularLinkedList()
    dll.insert_after_current(1)
    dll.insert_after_current(2)
    dll.insert_after_current(3)
    assert dll.size == 3
    assert dll.to_list() == [1, 3, 2]

    dll.move_forward(1)
    assert dll.current is not None
    removed = dll.remove_current()
    assert removed in {2, 3, 1}
    assert dll.size == 2


def test_move_modulo() -> None:
    dll = DoublyCircularLinkedList([0, 1, 2, 3])
    assert dll.current is not None
    assert dll.current.value == 0

    dll.move_forward(5)
    assert dll.current.value == 1

    dll.move_backward(6)
    assert dll.current.value == 3

