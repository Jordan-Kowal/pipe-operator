import inspect
import types
from typing import Callable


def is_lambda(f: Callable) -> bool:
    """Check if a function is a lambda function."""
    return isinstance(f, types.LambdaType) and f.__name__ == "<lambda>"


def is_async_function(f: Callable) -> bool:
    return inspect.iscoroutinefunction(f)


def is_one_arg_lambda(f: Callable) -> bool:
    """Check if a function is a lambda with exactly and only 1 positional parameter."""
    sig = inspect.signature(f)
    return is_lambda(f) and len(sig.parameters) == 1
