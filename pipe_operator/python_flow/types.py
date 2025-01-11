from typing import (
    Awaitable,
    Callable,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")
TOutput = TypeVar("TOutput")

SyncCallable: TypeAlias = Callable[Concatenate[TInput, FuncParams], TOutput]
AsyncCallable: TypeAlias = Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]]
PipeableCallable: TypeAlias = Union[
    Callable[Concatenate[TInput, FuncParams], TOutput],
    Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]],
]

TValue = TypeVar("TValue")
TNewValue = TypeVar("TNewValue")

TaskId: TypeAlias = Union[str, int]
