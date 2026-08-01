from collections.abc import Callable, Coroutine
from typing import (
    Any,
    Concatenate,
    TypeAlias,
    TypeVar,
)

from typing_extensions import ParamSpec

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")
TOutput = TypeVar("TOutput")

SyncCallable: TypeAlias = Callable[Concatenate[TInput, FuncParams], TOutput]
AsyncCallable: TypeAlias = Callable[
    Concatenate[TInput, FuncParams], Coroutine[Any, Any, TOutput]
]
PipeableCallable: TypeAlias = (
    SyncCallable[TInput, FuncParams, TOutput]
    | AsyncCallable[TInput, FuncParams, TOutput]
)

TValue = TypeVar("TValue")
TNewValue = TypeVar("TNewValue")

TaskId: TypeAlias = str | int
