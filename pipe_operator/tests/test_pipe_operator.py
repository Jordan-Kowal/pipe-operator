from typing import no_type_check
import unittest

from pipe_operator import pipes, tap


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
    @pipes
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


@pipes
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


class PipeOperatorTestCase(unittest.TestCase):
    # ------------------------------
    # Basic workflow
    # ------------------------------
    @no_type_check
    @pipes
    def test_class_calls(self) -> None:
        op = 1 >> BasicClass >> _.value >> BasicClass()
        self.assertIsInstance(op, BasicClass)
        self.assertEqual(op.value, 1)

    @no_type_check
    @pipes
    def test_attribute_calls(self) -> None:
        op = 33 >> BasicClass >> _.value
        self.assertEqual(op, 33)
        op = 33 >> BasicClass >> _.get_value_property
        self.assertEqual(op, 33)

    @no_type_check
    @pipes
    def test_method_calls(self) -> None:
        op = 33 >> BasicClass >> _.get_value_method()
        self.assertEqual(op, 33)
        op = 33 >> BasicClass >> _.get_value_plus_arg(10)
        self.assertEqual(op, 43)

    @no_type_check
    @pipes
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
    @pipes
    def test_function_calls(self) -> None:
        op = 1 >> double >> double() >> add(1) >> _sum(2, 3)
        self.assertEqual(op, 10)

    @no_type_check
    @pipes
    def test_lambda_calls(self) -> None:
        op = 2 >> (lambda a: a**2) >> (lambda a: a**2)
        self.assertEqual(op, 16)

    @no_type_check
    @pipes
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
            >> double
            >> tap(double)
            >> double()
            >> add(1)
            >> _sum(2, 3)
            >> (lambda a: a * 2)
        )
        self.assertEqual(op, 140)

    # ------------------------------
    # Ways to apply the decorator
    # ------------------------------
    @no_type_check
    @pipes
    def test_decorated_method(self) -> None:
        instance = ClassWithDecoratedMethod(1)
        op = instance.compute_score()
        self.assertEqual(op, 928)

    @no_type_check
    @pipes
    def test_decorated_class(self) -> None:
        instance = DecoratedClass(1)
        op = instance.compute_score()
        self.assertEqual(op, 928)

    @no_type_check
    @pipes
    def test_does_not_propagate(self) -> None:
        # rshift uses the `>>` operator, and it should behave normally
        result = rshift(1000, 4)
        self.assertEqual(result, 62)
        result = 1000 >> rshift(4)
        self.assertEqual(result, 62)

    @no_type_check
    @pipes()
    def test_can_be_called_with_parenthesis(self) -> None:
        foo = 10
        op = 33 >> double >> add(10) >> _ + foo
        self.assertEqual(op, 86)

    @no_type_check
    @pipes(placeholder="__", lambda_var="foo")
    def test_can_be_called_with_custom_params(self) -> None:
        foo = 10
        # The `foo` from `__ + foo` will be overwritten by our `lambda_var` with the same name
        op = 33 >> double >> add(10) >> __ + foo
        self.assertEqual(op, 152)

    # ------------------------------
    # Others
    # ------------------------------
    @no_type_check
    @pipes
    def test_tap(self) -> None:
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
