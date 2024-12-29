import asyncio
import time
from unittest import TestCase
from unittest.mock import Mock, patch

from pipe_operator.python_flow.base import (
    PipeEnd,
    PipeStart,
)
from pipe_operator.python_flow.pipes.asynchronous import AsyncPipe
from pipe_operator.python_flow.pipes.basics import Pipe, Tap
from pipe_operator.python_flow.pipes.threads import (
    ThreadPipe,
    ThreadWait,
)
from pipe_operator.shared.exceptions import PipeError


async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


def add_one(value: int) -> int:
    time.sleep(0.1)
    return value + 1


def to_string(x: int) -> str:
    return str(x)


def double(x: int) -> int:
    return x * 2


def duplicate_string(x: str) -> str:
    return f"{x}{x}"


def compute(x: int, y: int, z: int = 0) -> int:
    return x + y + z


def _sum(*args: int) -> int:
    return sum(args)


class BasicClass:
    def __init__(self, value: int) -> None:
        self.value = value

    def increment(self) -> None:
        self.value += 1

    @property
    def get_value_property(self) -> int:
        return self.value

    def get_value_method(self) -> int:
        return self.value

    def get_value_plus_arg(self, value: int) -> int:
        return self.value + value

    @classmethod
    def get_double(cls, instance: "BasicClass") -> "BasicClass":
        return BasicClass(instance.value * 2)


class PipeTestCase(TestCase):
    # ------------------------------
    # Errors
    # ------------------------------
    def test_pipe_does_not_support_multiple_args_lambdas(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Pipe(lambda x, _y: x + 1) >> PipeEnd()  # type: ignore

    def test_pipe_does_not_support_async_functions(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Pipe(async_add_one) >> PipeEnd()

    # ------------------------------
    # Workflows
    # ------------------------------
    def test_with_functions(self) -> None:
        op: int = (
            PipeStart("3")
            >> Pipe(duplicate_string)  # function
            >> Pipe(int)  # function
            >> Pipe(compute, 30, z=10)  # function with args/kwargs
            >> Pipe(_sum, 5, 10)  # function with no positional args  # type: ignore
            >> Pipe(lambda x: x + 1)  # lambda
            >> Pipe[int, [], int](lambda x: _sum(x, 5, 10))  # typed lambda
            >> PipeEnd()
        )
        self.assertEqual(op, 104)

    def test_with_classes(self) -> None:
        op = (
            PipeStart(3)
            >> Pipe(BasicClass)  # class
            >> Pipe(BasicClass.get_double)  # classmethod
            >> Pipe(BasicClass.get_value_method)  # method
            >> Pipe(BasicClass)  # class
            >> Pipe[BasicClass, [], int](lambda x: x.value)  # lambda for attribute
            >> PipeEnd()
        )
        self.assertEqual(op, 6)

    # ------------------------------
    # Debug
    # ------------------------------
    def test_debug(self) -> None:
        with patch("builtins.print") as mock_print:
            instance = (
                PipeStart(3, debug=True)
                >> Pipe(double)
                >> Tap(lambda x: mock_print(x))
                >> Pipe(double)
            )
            op = instance >> PipeEnd()
            self.assertEqual(op, 12)
            self.assertListEqual(instance.history, [3, 6, 6, 12])
        self.assertEqual(mock_print.call_count, 5)

    def test_not_debug(self) -> None:
        with patch("builtins.print") as mock_print:
            instance = (
                PipeStart(3)
                >> Pipe(double)
                >> Tap(lambda x: mock_print(x))
                >> Pipe(double)
            )
            op = instance >> PipeEnd()
            self.assertEqual(op, 12)
            self.assertListEqual(instance.history, [])
        self.assertEqual(mock_print.call_count, 1)  # The one from `Tap`

    # ------------------------------
    # Complex workflow
    # ------------------------------
    def test_complex(self) -> None:
        start = time.perf_counter()

        op = (
            PipeStart("3")  # start
            >> Pipe(duplicate_string)  # function
            >> ThreadPipe("t1", lambda _: time.sleep(0.2))  # thread
            >> Pipe(int)  # function
            >> AsyncPipe(async_add_one)  # async
            >> ThreadPipe("t2", double)  # thread
            >> Tap(compute, 2000, z=10)  # function with args
            >> Pipe(lambda x: x + 1)  # lambda
            >> Pipe(BasicClass)  # class
            >> Pipe(BasicClass.get_double)  # classmethod
            >> Tap(BasicClass.increment)  # tap + method that updates original object
            >> Pipe(BasicClass.get_value_method)  # method
            >> Pipe[int, [], int](lambda x: _sum(x, 4, 5, 6))  # typed lambda
            >> ThreadWait()  # thread join
            >> PipeEnd()  # end
        )

        delta = time.perf_counter() - start
        self.assertTrue(delta > 0.2)
        self.assertTrue(delta < 0.3)
        self.assertEqual(op, 86)


class TapTestCase(TestCase):
    def test_tap(self) -> None:
        mock = Mock()
        op = (
            PipeStart(3)
            >> Tap(lambda x: [x])  # tap + lambda
            >> Pipe(double)
            >> Tap(to_string)  # tap + function
            >> Pipe(double)
            >> Tap(compute, 2000, z=10)  # tap + function with args
            >> Tap(lambda x: mock(x))  # tap + lambda
            >> Pipe(double)
            >> PipeEnd()
        )
        self.assertEqual(op, 24)
        mock.assert_called_once_with(12)

    def test_does_not_support_async_functions(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Tap(async_add_one) >> PipeEnd()

    def test_does_not_support_multiple_args_lambdas(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Tap(lambda x, _y: x + 1) >> PipeEnd()  # type: ignore


class ThreadTestCase(TestCase):
    def test_with_threads_without_join(self) -> None:
        start = time.perf_counter()
        op = (
            PipeStart(3)
            >> ThreadPipe("t1", add_one)
            >> ThreadPipe("t2", lambda _: time.sleep(0.2))
            >> PipeEnd()
        )
        delta = time.perf_counter() - start
        # We did not wait for the threads to finish
        self.assertTrue(delta < 0.1)
        self.assertEqual(op, 3)

    def test_with_threads_with_some_joins(self) -> None:
        start = time.perf_counter()
        op = (
            PipeStart(3)
            >> ThreadPipe("t1", lambda _: time.sleep(0.1))
            >> ThreadPipe("t2", lambda _: time.sleep(0.2))
            >> ThreadWait(["t1"])
            >> PipeEnd()
        )
        delta = time.perf_counter() - start
        # We waited for the 1s thread only
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 3)

    def test_with_threads_with_join_all(self) -> None:
        start = time.perf_counter()
        op = (
            PipeStart(3)
            >> ThreadPipe("t1", lambda _: time.sleep(0.1))
            >> ThreadPipe("t2", lambda _: time.sleep(0.2))
            >> ThreadWait()
            >> PipeEnd()
        )
        delta = time.perf_counter() - start
        # We waited for all threads
        self.assertTrue(delta > 0.2)
        self.assertTrue(delta < 0.3)
        self.assertEqual(op, 3)

    def test_with_threads_with_unknown_thread_id(self) -> None:
        with self.assertRaises(PipeError):
            _ = (
                PipeStart(3)
                >> ThreadPipe("t1", lambda _: time.sleep(0.2))
                >> ThreadWait(["t2"])
                >> PipeEnd()
            )

    def test_with_threads_with_duplicated_thread_id(self) -> None:
        with self.assertRaises(PipeError):
            _ = (
                PipeStart(3)
                >> ThreadPipe("t1", lambda _: time.sleep(0.2))
                >> ThreadPipe("t1", lambda _: time.sleep(0.2))
                >> PipeEnd()
            )

    def test_does_not_support_async_functions(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> ThreadPipe("t1", async_add_one) >> PipeEnd()

    def test_does_not_support_multiple_args_lambdas(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> ThreadPipe("t1", lambda x, _y: x + 1) >> PipeEnd()  # type: ignore


class AsyncTestCase(TestCase):
    def test_async_pipe(self) -> None:
        start = time.perf_counter()
        op = PipeStart(3) >> AsyncPipe(async_add_one) >> PipeEnd()
        delta = time.perf_counter() - start
        # We waited for the 1s from async_add_one
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 4)

    def test_does_not_support_regular_functions(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> AsyncPipe(add_one) >> PipeEnd()  # type: ignore
