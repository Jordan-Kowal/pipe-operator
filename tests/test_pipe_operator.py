from typing import no_type_check
import unittest

from pipe_operator import pipes


def add(a: int, b: int) -> int:
    return a + b


def double(a: int) -> int:
    return 2 * a


def _sum(*args: int) -> int:
    return sum(args)


class BasicClass:
    def __init__(self, value: int) -> None:
        self.value = value

    def increment(self) -> None:
        self.value += 1

    def get_value(self) -> int:
        return self.value


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
    @no_type_check
    @pipes
    def test_one_arg(self) -> None:
        op = 1 >> double >> double()
        self.assertEqual(op, 4)

    @no_type_check
    @pipes
    def test_two_plus_arg(self) -> None:
        op = 1 >> add(5) >> add(10)
        self.assertEqual(op, 16)

    @no_type_check
    @pipes
    def test_unlimited_args(self) -> None:
        op = 1 >> _sum >> _sum(2, 3)
        self.assertEqual(op, 6)

    @no_type_check
    @pipes
    def test_lambda(self) -> None:
        op = 2 >> (lambda a: a**2) >> (lambda a: a**2)
        self.assertEqual(op, 16)

    @no_type_check
    @pipes
    def test_class_call(self) -> None:
        op = 1 >> BasicClass
        self.assertIsInstance(op, BasicClass)
        self.assertEqual(op.value, 1)

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
    def test_complex(self) -> None:
        pass
