from typing import (
    Awaitable,
    Callable,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.python_flow.base import PipeStart, _BasePipe
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import is_async_function

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

TaskId: TypeAlias = Union[str, int]


class AsyncPipe(_BasePipe[TInput, FuncParams, TOutput]):
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

    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        """Overrides typing for `f` to allow async functions."""
        super().__init__(f, *args, **kwargs)  # type: ignore

    def validate_f(self) -> None:
        """f must be an async function."""
        if not is_async_function(self.f):
            raise PipeError(
                "`AsyncPipe` only supports async functions. Use `Pipe` for regular functions."
            )

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TOutput]:
        """Delegates to `PipeStart.__rshift__`"""
        return other.__rshift__(self)
