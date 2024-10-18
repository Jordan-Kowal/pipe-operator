from unittest import TestCase

from pipe_operator.shared.utils import (
    function_needs_parameters,
    is_lambda,
    is_one_arg_lambda,
)


def not_lambda_func(x: int) -> int:
    return x


def _sum(*args: int) -> int:
    return sum(args)


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

    def test_function_needs_parameters(self) -> None:
        # No required parameters
        self.assertFalse(function_needs_parameters(lambda: None))
        self.assertFalse(function_needs_parameters(lambda *args: args))
        self.assertFalse(function_needs_parameters(lambda **kwargs: kwargs))
        self.assertFalse(
            function_needs_parameters(lambda *args, **kwargs: [args, kwargs])
        )
        self.assertFalse(function_needs_parameters(_sum))
        # Required parameters
        self.assertTrue(function_needs_parameters(lambda x: x))
        self.assertTrue(function_needs_parameters(lambda x, y: x + y))
        self.assertTrue(function_needs_parameters(lambda x, *_args, **_kwargs: x))
        self.assertTrue(function_needs_parameters(not_lambda_func))
