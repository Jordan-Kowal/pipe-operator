from unittest import TestCase
from unittest.mock import Mock, patch

from pipe_operator.python_like.pipe import Pipe, PipeStart, Tap


def double(x: int) -> int:
    return x * 2


def double_str(x: str) -> str:
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


class PipeTestCase(TestCase):
    def test_with_functions(self) -> None:
        op = (
            PipeStart("3")
            >> Pipe(double_str)
            >> Pipe(int)
            >> Pipe(double)
            >> Pipe(compute, 30, z=10)
            >> Pipe(_sum, 4, 5)
            >> Pipe(lambda x: x + 1)
        )
        self.assertEqual(op.value, 116)

    def test_with_tap(self) -> None:
        mock = Mock()
        op = (
            PipeStart(3)
            >> Tap(lambda x: [x])
            >> Pipe(double)
            >> Tap(str)
            >> Pipe(double)
            >> Tap(compute, 2000, z=10)
            >> Tap(lambda x: mock(x))
            >> Pipe(double)
        )
        self.assertEqual(op.value, 24)
        mock.assert_called_once_with(12)

    def test_debug(self) -> None:
        with patch("builtins.print") as mock_print:
            op = (
                PipeStart(3, debug=True)
                >> Pipe(double)
                >> Tap(lambda x: mock_print(x))
                >> Pipe(double)
            )
            self.assertEqual(op.value, 12)
        self.assertEqual(mock_print.call_count, 5)

    def test_complex(self) -> None:
        op = (
            PipeStart("3")
            >> Pipe(double_str)
            >> Pipe(int)
            >> Tap(compute, 2000, z=10)
            >> Pipe(lambda x: x + 1)
            >> Pipe(_sum, 4, 5, 6)
        )
        self.assertEqual(op.value, 49)
