import unittest

from analog_clock_app.domain.structures.doubly_circular_list import (
    DoublyCircularLinkedList,
)


class TestDoublyCircularLinkedList(unittest.TestCase):
    def test_empty_list(self) -> None:
        dll: DoublyCircularLinkedList[int] = DoublyCircularLinkedList()
        self.assertEqual(dll.size, 0)
        self.assertTrue(dll.is_empty())
        self.assertEqual(dll.to_list(), [])
        with self.assertRaises(IndexError):
            dll.move_forward(1)
        with self.assertRaises(IndexError):
            dll.remove_current()

    def test_insert_and_to_list(self) -> None:
        dll: DoublyCircularLinkedList[int] = DoublyCircularLinkedList()
        dll.insert_after_current(1)
        self.assertEqual(dll.to_list(), [1])
        dll.insert_after_current(2)
        dll.insert_after_current(3)
        self.assertEqual(dll.size, 3)
        self.assertEqual(dll.to_list(), [1, 3, 2])

    def test_move_forward_backward_modulo(self) -> None:
        dll = DoublyCircularLinkedList([0, 1, 2, 3])
        self.assertEqual(dll.current.value, 0)
        dll.move_forward(5)
        self.assertEqual(dll.current.value, 1)
        dll.move_backward(6)
        self.assertEqual(dll.current.value, 3)

    def test_remove_current_updates_head_and_current(self) -> None:
        dll = DoublyCircularLinkedList([10, 20, 30])
        self.assertEqual(dll.to_list(), [10, 20, 30])
        removed = dll.remove_current()
        self.assertEqual(removed, 10)
        self.assertEqual(dll.head.value, 20)
        self.assertEqual(dll.current.value, 20)
        self.assertEqual(dll.size, 2)
        self.assertEqual(dll.to_list(), [20, 30])

        dll.move_forward(1)
        self.assertEqual(dll.current.value, 30)
        removed2 = dll.remove_current()
        self.assertEqual(removed2, 30)
        self.assertEqual(dll.size, 1)
        self.assertEqual(dll.to_list(), [20])


if __name__ == "__main__":
    unittest.main()

