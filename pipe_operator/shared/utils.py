import inspect
import types
from typing import Callable


def is_lambda(f: Callable) -> bool:
    return isinstance(f, types.LambdaType) and f.__name__ == "<lambda>"


def is_one_arg_lambda(f: Callable) -> bool:
    sig = inspect.signature(f)
    return is_lambda(f) and len(sig.parameters) == 1
