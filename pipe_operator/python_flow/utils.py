import inspect
from typing import Any, Callable, Coroutine

from typing_extensions import TypeIs

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
) -> TypeIs[AsyncCallable[TInput, FuncParams, TOutput]]:
    """Checks if a function is "pipeable asynchronous" and provides a TypeIs for it."""
    return _is_async_function(f)


def is_sync_pipeable(
    f: PipeableCallable[TInput, FuncParams, TOutput],
) -> TypeIs[SyncCallable[TInput, FuncParams, TOutput]]:
    """Checks if a pipeable function is "pipeable synchronous" and provides a TypeIs for it."""
    return not _is_async_function(f)


def _is_async_function(
    f: Callable[..., Any],
) -> TypeIs[Callable[..., Coroutine[Any, Any, Any]]]:
    """Checks if a function is asynchronous and provides a TypeIs for it."""
    return inspect.iscoroutinefunction(f)
