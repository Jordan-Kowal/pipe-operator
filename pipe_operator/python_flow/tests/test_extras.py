import asyncio
from unittest import TestCase
from unittest.mock import Mock

from pipe_operator.python_flow.base import (
    Pipe,
    PipeEnd,
    PipeStart,
)
from pipe_operator.python_flow.extras import Tap
from pipe_operator.shared.exceptions import PipeError


async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


def double(x: int) -> int:
    return x * 2


def to_string(x: int) -> str:
    return str(x)


def compute(x: int, y: int, z: int = 0) -> int:
    return x + y + z


class BasicClass:
    def __init__(self, value: int) -> None:
        self.value = value


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
