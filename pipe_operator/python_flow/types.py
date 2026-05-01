from typing import (
    Any,
    Callable,
    Coroutine,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")
TOutput = TypeVar("TOutput")

SyncCallable: TypeAlias = Callable[Concatenate[TInput, FuncParams], TOutput]
AsyncCallable: TypeAlias = Callable[
    Concatenate[TInput, FuncParams], Coroutine[Any, Any, TOutput]
]
PipeableCallable: TypeAlias = Union[
    SyncCallable[TInput, FuncParams, TOutput],
    AsyncCallable[TInput, FuncParams, TOutput],
]

TValue = TypeVar("TValue")
TNewValue = TypeVar("TNewValue")

TaskId: TypeAlias = Union[str, int]
