import asyncio
import time
from unittest import TestCase
from unittest.mock import patch

from pipe_operator.python_flow.asynchronous import AsyncPipe
from pipe_operator.python_flow.base import (
    Pipe,
    PipeEnd,
    PipeStart,
)
from pipe_operator.python_flow.extras import Tap
from pipe_operator.python_flow.threads import (
    ThreadPipe,
    ThreadWait,
)
from pipe_operator.shared.exceptions import PipeError


async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


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
