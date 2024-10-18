import inspect
import types
from typing import Callable


def is_lambda(f: Callable) -> bool:
    return isinstance(f, types.LambdaType) and f.__name__ == "<lambda>"


def is_one_arg_lambda(f: Callable) -> bool:
    sig = inspect.signature(f)
    return is_lambda(f) and len(sig.parameters) == 1


def function_needs_parameters(f: Callable) -> bool:
    sig = inspect.signature(f)
    for _name, param in sig.parameters.items():
        if param.default == inspect.Parameter.empty and param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            return True
    return False
