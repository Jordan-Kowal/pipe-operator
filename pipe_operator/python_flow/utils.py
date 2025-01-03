import inspect
from typing import Any, Callable, Coroutine, TypeGuard

from pipe_operator.python_flow.types import (
    AsyncCallable,
    FuncParams,
    PipeableCallable,
    SyncCallable,
    TInput,
    TOutput,
)


def is_async_pipeable(
    f: PipeableCallable[TInput, FuncParams, TOutput],
) -> TypeGuard[AsyncCallable[TInput, FuncParams, TOutput]]:
    return _is_async_function(f)


def is_sync_pipeable(
    f: PipeableCallable[TInput, FuncParams, TOutput],
) -> TypeGuard[SyncCallable[TInput, FuncParams, TOutput]]:
    return not _is_async_function(f)


def _is_async_function(f: Callable[..., Any]) -> TypeGuard[Coroutine]:
    return inspect.iscoroutinefunction(f)
