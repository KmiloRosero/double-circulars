import unittest

from analog_clock_app.domain.structures import (
    DoublyLinkedList,
    DynamicArray,
    Queue,
    SinglyLinkedList,
    Stack,
)


class TestDynamicArray(unittest.TestCase):
    def test_append_pop(self) -> None:
        arr = DynamicArray[int]()
        self.assertTrue(arr.is_empty())
        arr.append(1)
        arr.append(2)
        self.assertEqual(arr.to_list(), [1, 2])
        self.assertEqual(arr.pop(), 2)
        self.assertEqual(arr.pop(), 1)
        self.assertTrue(arr.is_empty())
        with self.assertRaises(IndexError):
            arr.pop()


class TestStack(unittest.TestCase):
    def test_lifo(self) -> None:
        s = Stack[int]()
        s.push(10)
        s.push(20)
        self.assertEqual(s.peek(), 20)
        self.assertEqual(s.pop(), 20)
        self.assertEqual(s.pop(), 10)
        self.assertTrue(s.is_empty())
        with self.assertRaises(IndexError):
            s.peek()


class TestQueue(unittest.TestCase):
    def test_fifo(self) -> None:
        q = Queue[int]()
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        self.assertEqual(q.peek(), 1)
        self.assertEqual(q.dequeue(), 1)
        self.assertEqual(q.dequeue(), 2)
        self.assertEqual(q.dequeue(), 3)
        self.assertTrue(q.is_empty())
        with self.assertRaises(IndexError):
            q.dequeue()

    def test_grows(self) -> None:
        q = Queue[int]()
        for i in range(100):
            q.enqueue(i)
        self.assertEqual(len(q), 100)
        for i in range(100):
            self.assertEqual(q.dequeue(), i)
        self.assertTrue(q.is_empty())


class TestSinglyLinkedList(unittest.TestCase):
    def test_append_pop_left(self) -> None:
        lst = SinglyLinkedList[int]()
        lst.append(1)
        lst.append(2)
        lst.append(3)
        self.assertEqual(lst.to_list(), [1, 2, 3])
        self.assertEqual(lst.pop_left(), 1)
        self.assertEqual(lst.pop_left(), 2)
        self.assertEqual(lst.pop_left(), 3)
        self.assertTrue(lst.is_empty())
        with self.assertRaises(IndexError):
            lst.pop_left()


class TestDoublyLinkedList(unittest.TestCase):
    def test_append_pop_ends(self) -> None:
        lst = DoublyLinkedList[int]([1, 2, 3])
        self.assertEqual(lst.to_list(), [1, 2, 3])
        self.assertEqual(lst.pop_left(), 1)
        self.assertEqual(lst.pop_right(), 3)
        self.assertEqual(lst.to_list(), [2])
        self.assertEqual(lst.pop_left(), 2)
        self.assertTrue(lst.is_empty())
        with self.assertRaises(IndexError):
            lst.pop_right()


if __name__ == "__main__":
    unittest.main()

