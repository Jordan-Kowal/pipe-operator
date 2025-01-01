import inspect
import types
from types import LambdaType
from typing import Any, Callable, Coroutine, TypeGuard


def is_lambda(f: Callable) -> TypeGuard[LambdaType]:
    """Check if a function is a lambda function."""
    return isinstance(f, types.LambdaType) and f.__name__ == "<lambda>"


def is_async_function(f: Callable) -> TypeGuard[Coroutine]:
    return inspect.iscoroutinefunction(f)


def is_single_arg_function(f: Callable) -> TypeGuard[Callable[[Any], Any]]:
    sig = inspect.signature(f)
    return len(sig.parameters) == 1


def is_one_arg_lambda(f: Callable) -> TypeGuard[Callable[[Any], Any]]:
    """Check if a function is a lambda with exactly and only 1 positional parameter."""
    return is_lambda(f) and is_single_arg_function(f)
