import inspect
import types
from types import LambdaType
from typing import Any, Callable

from typing_extensions import TypeGuard


def is_lambda(f: Callable) -> TypeGuard[LambdaType]:
    """Check if a function is a lambda function."""
    return isinstance(f, types.LambdaType) and f.__name__ == "<lambda>"


def is_one_arg_lambda(f: Callable) -> TypeGuard[Callable[[Any], Any]]:
    """Check if a function is a lambda with exactly and only 1 positional parameter."""
    sig = inspect.signature(f)
    return is_lambda(f) and len(sig.parameters) == 1
