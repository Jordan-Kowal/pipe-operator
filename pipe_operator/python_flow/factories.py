from typing import Union, overload

from pipe_operator.python_flow.classes import (
    AsyncPipe,
    Pipe,
)
from pipe_operator.python_flow.types import (
    AsyncCallable,
    FuncParams,
    PipeableCallable,
    SyncCallable,
    TInput,
    TOutput,
)
from pipe_operator.python_flow.utils import (
    is_async_pipeable,
    is_sync_pipeable,
)
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import is_lambda


# region pipe
@overload
def pipe(
    f: SyncCallable[TInput, FuncParams, TOutput],
    *args: FuncParams.args,
    **kwargs: FuncParams.kwargs,
) -> Pipe[TInput, FuncParams, TOutput]: ...


@overload
def pipe(
    f: AsyncCallable[TInput, FuncParams, TOutput],
    *args: FuncParams.args,
    **kwargs: FuncParams.kwargs,
) -> AsyncPipe[TInput, FuncParams, TOutput]: ...


def pipe(
    f: PipeableCallable[TInput, FuncParams, TOutput],
    *args: FuncParams.args,
    **kwargs: FuncParams.kwargs,
) -> Union[Pipe[TInput, FuncParams, TOutput], AsyncPipe[TInput, FuncParams, TOutput]]:
    if is_lambda(f):
        raise PipeError("`pipe` does not support lambda functions. Use `then` instead.")
    if is_sync_pipeable(f):
        return Pipe(f, *args, **kwargs)
    if is_async_pipeable(f):
        return AsyncPipe(f, *args, **kwargs)
    raise PipeError("Unsupported function provided to `pipe`.")
