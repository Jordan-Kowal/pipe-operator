from unittest import TestCase

from pipe_operator.python_like.utils import is_lambda


def not_lambda_func(x: int) -> int:
    return x


class NotLambdaClass:
    def func(self) -> int:
        return 0


class UtilsTestCase(TestCase):
    def test_is_lambda(self) -> None:
        # Lambda
        self.assertTrue(is_lambda(lambda x: x))
        self.assertTrue(is_lambda(lambda: None))
        # Not Lambda
        self.assertFalse(is_lambda(not_lambda_func))
        self.assertFalse(is_lambda(NotLambdaClass))
        self.assertFalse(is_lambda(NotLambdaClass.func))
