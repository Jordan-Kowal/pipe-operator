import types
from typing import Callable


def is_lambda(func: Callable) -> bool:
    return isinstance(func, types.LambdaType) and func.__name__ == "<lambda>"
