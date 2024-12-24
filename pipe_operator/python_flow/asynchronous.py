# import asyncio


# async def main() -> int:
#     print("hello")
#     await asyncio.sleep(2)
#     print("world")
#     return 33


# value = asyncio.run(main())
# print(value)


import inspect
from typing import (
    Awaitable,
    Callable,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.python_flow.base import Pipe, PipeStart
from pipe_operator.shared.exceptions import PipeError

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

TaskId: TypeAlias = Union[str, int]


class AsyncPipe(Pipe[TInput, FuncParams, TOutput]):
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
        kwargs["_async"] = True
        super().__init__(f, *args, **kwargs)  # type: ignore

    def check_f(self) -> None:
        super().check_f()
        if not inspect.iscoroutinefunction(self.f):
            raise PipeError(
                "`AsyncPipe` only supports async functions. Use `Pipe` for regular functions."
            )

    def __rrshift__(self, other: "PipeStart") -> PipeStart[TOutput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)
