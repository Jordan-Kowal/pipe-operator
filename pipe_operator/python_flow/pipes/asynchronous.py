import asyncio
from typing import (
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec, TypeAlias

from pipe_operator.python_flow.base import PipeStart
from pipe_operator.python_flow.pipes.basics import _AsyncPipeable

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

TaskId: TypeAlias = Union[str, int]


class AsyncPipe(_AsyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element to run and wait for async functions (through asyncio).
    Similar to the regular `Pipe` but for async functions.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]]): The async function that will be called with asyncio.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If the `f` is not an async function.

    Examples:
        >>> import asyncio
        >>> async def add_one(value: int) -> int:
        ...     await asyncio.sleep(0.1)
        ...     return value + 1
        >>> PipeStart(3) >> AsyncPipe(add_one) >> PipeEnd()
        4
    """

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TOutput]:
        value = asyncio.run(self.f(other.value, *self.args, **self.kwargs))  # type: ignore
        other.value = value
        return other  # type: ignore
