import types
from typing import no_type_check
from unittest import TestCase
from unittest.mock import Mock

from pipe_operator.elixir_flow.pipe import elixir_pipe, tap, then


def add(a: int, b: int) -> int:
    return a + b


def double(a: int) -> int:
    return 2 * a


def _sum(*args: int) -> int:
    return sum(args)


def rshift(a: int, b: int) -> int:
    return a >> b


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


class ClassWithDecoratedMethod(BasicClass):
    @no_type_check
    @elixir_pipe
    def compute_score(self) -> int:
        return (
            self.value
            >> double
            >> add(10)
            >> _sum(1, 2, 3, 4)
            >> pow(2)
            >> add(-20)
            >> double
        )


@elixir_pipe
class DecoratedClass(BasicClass):
    @no_type_check
    def compute_score(self) -> int:
        return (
            self.value
            >> double
            >> add(10)
            >> _sum(1, 2, 3, 4)
            >> pow(2)
            >> add(-20)
            >> double
        )


class PipeOperatorTestCase(TestCase):
    # ------------------------------
    # Basic workflow
    # ------------------------------

    @no_type_check
    @elixir_pipe
    def test_class_calls(self) -> None:
        op = 1 >> BasicClass >> _.value >> BasicClass()
        self.assertIsInstance(op, BasicClass)
        self.assertEqual(op.value, 1)

    @no_type_check
    @elixir_pipe
    def test_attribute_calls(self) -> None:
        op = 33 >> BasicClass >> _.value
        self.assertEqual(op, 33)
        op = 33 >> BasicClass >> _.get_value_property
        self.assertEqual(op, 33)

    @no_type_check
    @elixir_pipe
    def test_method_calls(self) -> None:
        op = 33 >> BasicClass >> _.get_value_method()
        self.assertEqual(op, 33)
        op = 33 >> BasicClass >> _.get_value_plus_arg(10)
        self.assertEqual(op, 43)

    @no_type_check
    @elixir_pipe
    def test_binary_operators(self) -> None:
        x = 50
        op = (
            1_000
            >> _ + 3
            >> double
            >> _ + _
            >> _ * 10 + 3
            >> 10 + _ - 5
            >> 10 - 12 + _
            >> 1 + _ + _ + 1
            >> _ + x
        )
        self.assertEqual(op, 80304)

    @no_type_check
    @elixir_pipe
    def test_f_strings(self) -> None:
        op = 50 >> f"value is {_}" >> f"And now is '{_}'"
        self.assertEqual(op, "And now is 'value is 50'")

    @no_type_check
    @elixir_pipe
    def test_struct_creations(self) -> None:
        op = 1 >> {1, _, 3} >> [_, {4}] >> {"value": _} >> (_, "other value in tuple")
        self.assertEqual(op, ({"value": [{1, 3}, {4}]}, "other value in tuple"))

    @no_type_check
    @elixir_pipe
    def test_comprehensions(self) -> None:
        op = (
            10
            >> [x for x in range(_) if x >= _ - 2]
            >> {x + 1 for x in _}
            >> {x: x + 1 for x in _}
            >> ((k, v) for k, v in _.items())
        )
        self.assertIsInstance(op, types.GeneratorType)
        self.assertEqual(list(op), [(9, 10), (10, 11)])

    @no_type_check
    @elixir_pipe
    def test_function_calls(self) -> None:
        op = 1 >> double >> double() >> add(1) >> _sum(2, 3)
        self.assertEqual(op, 10)

    @no_type_check
    @elixir_pipe
    def test_lambda_calls(self) -> None:
        op = 2 >> (lambda a: a**2) >> (lambda a: a**2)
        self.assertEqual(op, 16)

    @no_type_check
    @elixir_pipe
    def test_complex(self) -> None:
        op = (
            1
            >> BasicClass
            >> _.value
            >> BasicClass()
            >> _.get_value_property
            >> BasicClass()
            >> _.get_value_method()
            >> BasicClass()
            >> _.get_value_plus_arg(10)
            >> 10 + _ - 5
            >> {_, 1, 2, 3}
            >> [x for x in _ if x > 4]
            >> (lambda x: x[0])
            >> double
            >> tap(double)
            >> double()
            >> add(1)
            >> _sum(2, 3)
            >> (lambda a: a * 2)
            >> then(lambda a: a + 1)
            >> f"value is {_}"
        )
        self.assertEqual(op, "value is 141")

    # ------------------------------
    # Ways to apply the decorator
    # ------------------------------

    @no_type_check
    @elixir_pipe
    def test_decorated_method(self) -> None:
        instance = ClassWithDecoratedMethod(1)
        op = instance.compute_score()
        self.assertEqual(op, 928)

    @no_type_check
    @elixir_pipe
    def test_decorated_class(self) -> None:
        instance = DecoratedClass(1)
        op = instance.compute_score()
        self.assertEqual(op, 928)

    @no_type_check
    @elixir_pipe
    def test_does_not_propagate(self) -> None:
        # rshift uses the `>>` operator, and it should behave normally
        result = rshift(1000, 4)
        self.assertEqual(result, 62)
        result = 1000 >> rshift(4)
        self.assertEqual(result, 62)

    @no_type_check
    @elixir_pipe()
    def test_can_be_called_with_parenthesis(self) -> None:
        foo = 10
        op = 33 >> double >> add(10) >> _ + foo
        self.assertEqual(op, 86)

    @no_type_check
    @elixir_pipe(placeholder="__", lambda_var="foo", operator="|", debug=True)
    def test_can_be_called_with_custom_params(self) -> None:
        print = Mock()
        foo = 10
        # The `foo` from `__ + foo` will be overwritten during our lambda
        op = 33 | double | add(10) | __ + foo
        self.assertEqual(op, 152)
        self.assertEqual(print.call_count, 4)

    # ------------------------------
    # Others
    # ------------------------------

    @no_type_check
    @elixir_pipe
    def test_with_tap(self) -> None:
        op = (
            4
            >> add(10)
            >> tap(lambda a: a**3)
            >> tap(double)
            >> double
            >> tap(lambda a: a**3)
            >> add(1)
        )
        self.assertEqual(op, 29)

    @no_type_check
    @elixir_pipe
    def test_with_then(self) -> None:
        op = 0 >> add(10) >> then(lambda a: a**2) >> double
        self.assertEqual(op, 200)


class TapTestCase(TestCase):
    def test_with_func(self) -> None:
        mock_func = Mock()
        results = tap(4, mock_func)
        self.assertEqual(results, 4)
        mock_func.assert_called_once_with(4)


class ThenTestCase(TestCase):
    def test_with_lambdas(self) -> None:
        op = then(4, lambda x: x + 1)
        self.assertEqual(op, 5)

    def test_should_raise_error_if_not_one_arg_lambda(self) -> None:
        with self.assertRaises(TypeError):
            then(4, double)
        with self.assertRaises(TypeError):
            then(4, BasicClass)
        with self.assertRaises(TypeError):
            then(4, lambda x, y: x + y)  # type: ignore
