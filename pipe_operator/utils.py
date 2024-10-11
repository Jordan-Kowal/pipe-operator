from typing import Any, Callable, TypeVar

T = TypeVar("T")


def tap(value: T, func_or_class: Callable[[T], Any]) -> T:
    func_or_class(value)
    return value
