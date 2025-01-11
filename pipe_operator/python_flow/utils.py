import inspect
from typing import Any, Callable, Coroutine

from typing_extensions import TypeGuard

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
    """Checks if a function is "pipeable asynchronous" and provides a TypeGuard for it."""
    return _is_async_function(f)


def is_sync_pipeable(
    f: PipeableCallable[TInput, FuncParams, TOutput],
) -> TypeGuard[SyncCallable[TInput, FuncParams, TOutput]]:
    """Checks if a pipeable function is "pipeable synchronous" and provides a TypeGuard for it."""
    return not _is_async_function(f)


def _is_async_function(f: Callable[..., Any]) -> TypeGuard[Coroutine]:
    """Checks if a function is asynchronous and provides a TypeGuard for it."""
    return inspect.iscoroutinefunction(f)
