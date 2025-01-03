import asyncio
from unittest import TestCase

from pipe_operator.shared.utils import (
    is_lambda,
    is_one_arg_lambda,
)


def not_lambda_func(x: int) -> int:
    return x


async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


class NotLambdaClass:
    def func(self) -> int:
        return 0


class UtilsTestCase(TestCase):
    def test_is_lambda(self) -> None:
        # Lambda
        self.assertTrue(is_lambda(lambda x: x))
        self.assertTrue(is_lambda(lambda x, y: x + y))
        self.assertTrue(is_lambda(lambda: None))
        # Not Lambda
        self.assertFalse(is_lambda(not_lambda_func))
        self.assertFalse(is_lambda(NotLambdaClass))
        self.assertFalse(is_lambda(NotLambdaClass.func))

    def test_is_one_arg_lambda(self) -> None:
        # Lambda
        self.assertTrue(is_one_arg_lambda(lambda x: x))
        # Not 1 arg Lambda
        self.assertFalse(is_one_arg_lambda(lambda x, y: x + y))
        self.assertFalse(is_one_arg_lambda(lambda: None))
        self.assertFalse(is_one_arg_lambda(not_lambda_func))
        self.assertFalse(is_one_arg_lambda(NotLambdaClass))
