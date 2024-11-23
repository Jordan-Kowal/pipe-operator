from unittest import TestCase
from unittest.mock import Mock

from pipe_operator.python_flow.base import (
    Pipe,
    PipeEnd,
    PipeStart,
)
from pipe_operator.python_flow.extras import Tap, Then
from pipe_operator.shared.exceptions import PipeError


def double(x: int) -> int:
    return x * 2


def compute(x: int, y: int, z: int = 0) -> int:
    return x + y + z


class BasicClass:
    def __init__(self, value: int) -> None:
        self.value = value


class ThenTestCase(TestCase):
    def test_then(self) -> None:
        op = (
            PipeStart("3")
            >> Then[str, int](lambda x: int(x) + 1)  # typed then/lambda
            >> Then[int, int](lambda x: double(x))  # typed then/lambda
            >> Then(lambda x: x)  # then/lambda
            >> PipeEnd()
        )
        self.assertEqual(op, 8)

    def test_only_supports_one_arg_lambdas(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Then(double) >> PipeEnd()
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Then(BasicClass) >> PipeEnd()
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> Then(lambda x, y: x + y) >> PipeEnd()  # type: ignore


class TapTestCase(TestCase):
    def test_tap(self) -> None:
        mock = Mock()
        op = (
            PipeStart(3)
            >> Tap(lambda x: [x])  # tap + lambda
            >> Pipe(double)
            >> Tap(str)  # tap + function
            >> Pipe(double)
            >> Tap(compute, 2000, z=10)  # tap + function with args
            >> Tap(lambda x: mock(x))  # tap + lambda
            >> Pipe(double)
            >> PipeEnd()
        )
        self.assertEqual(op, 24)
        mock.assert_called_once_with(12)
