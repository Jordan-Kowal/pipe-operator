from unittest import TestCase
from unittest.mock import Mock, patch

from pipe_operator.python_flow.pipe import Pipe, PipeArgs, PipeEnd, PipeStart, Tap, Then


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


class PipeArgsestCase(TestCase):
    # ------------------------------
    # Settings
    # ------------------------------
    def test_pipe_does_not_support_lambdas(self) -> None:
        with self.assertRaises(TypeError):
            _ = PipeStart(3) >> Pipe(lambda x: x + 1) >> PipeEnd()

    def test_then_only_supports_one_arg_lambdas(self) -> None:
        with self.assertRaises(TypeError):
            _ = PipeStart(3) >> Then(double) >> PipeEnd()
        with self.assertRaises(TypeError):
            _ = PipeStart(3) >> Then(BasicClass) >> PipeEnd()
        with self.assertRaises(TypeError):
            _ = PipeStart(3) >> Then(lambda x, y: x + y) >> PipeEnd()  # type: ignore

    def test_pipeargs_only_supports_functions_with_no_required_args(self) -> None:
        with self.assertRaises(TypeError):
            _ = PipeStart(3) >> PipeArgs(double) >> PipeEnd()  # type: ignore
        with self.assertRaises(TypeError):
            _ = PipeStart(3) >> PipeArgs(BasicClass) >> PipeEnd()  # type: ignore
        with self.assertRaises(TypeError):
            _ = (
                PipeStart(3)
                >> PipeArgs(lambda x, *_args, **_kwargs: x + 1)  # noqa # type: ignore
                >> PipeEnd()
            )
        op = PipeStart(3) >> PipeArgs(_sum, 4) >> PipeEnd()
        self.assertEqual(op, 7)

    # ------------------------------
    # Workflows
    # ------------------------------
    def test_with_functions(self) -> None:
        op: int = (
            PipeStart("3")
            >> Pipe(duplicate_string)  # function
            >> Pipe(int)  # function
            >> Pipe(compute, 30, z=10)  # function with args
            >> PipeArgs(_sum, 5, 10)  # pipe args
            >> PipeEnd()
        )
        self.assertEqual(op, 88)

    def test_with_then(self) -> None:
        op = (
            PipeStart("3")
            >> Then[str, int](lambda x: int(x) + 1)  # typed then/lambda
            >> Then[int, int](lambda x: double(x))  # typed then/lambda
            >> Then(lambda x: x)  # then/lambda
            >> PipeEnd()
        )
        self.assertEqual(op, 8)

    def test_with_classes(self) -> None:
        op = (
            PipeStart(3)
            >> Pipe(BasicClass)  # class
            >> Pipe(BasicClass.get_double)  # classmethod
            >> Pipe(BasicClass.get_value_method)  # method
            >> PipeEnd()
        )
        self.assertEqual(op, 6)

    def test_with_tap(self) -> None:
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

    def test_debug(self) -> None:
        with patch("builtins.print") as mock_print:
            op = (
                PipeStart(3, debug=True)
                >> Pipe(double)
                >> Tap(lambda x: mock_print(x))
                >> Pipe(double)
                >> PipeEnd()
            )
            self.assertEqual(op, 12)
        self.assertEqual(mock_print.call_count, 5)

    def test_complex(self) -> None:
        op = (
            PipeStart("3")  # start
            >> Pipe(duplicate_string)  # function
            >> Pipe(int)  # function
            >> Tap(compute, 2000, z=10)  # function with args
            >> Then(lambda x: x + 1)  # then/lambda
            >> Pipe(BasicClass)  # class
            >> Pipe(BasicClass.get_double)  # classmethod
            >> Tap(BasicClass.increment)  # tap + method that updates original object
            >> Pipe(BasicClass.get_value_method)  # method
            >> Then[int, int](lambda x: x * 2)  # typed then/lambda
            >> PipeArgs(_sum, 4, 5, 6)  # pipe args
            >> PipeEnd()  # end
        )
        self.assertEqual(op, 153)
