from unittest import TestCase

from pipe_operator.python_like.pipe import Pipe, PipeValue


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
            PipeValue("3")
            >> Pipe(double_str)
            >> Pipe(int)
            >> Pipe(double)
            >> Pipe(compute, 30, z=10)
            >> Pipe(_sum, 4, 5)
            >> Pipe(lambda x: x + 1)
        )
        self.assertEqual(op.value, 116)
