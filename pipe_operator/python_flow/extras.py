from typing import (
    Callable,
    Generic,
    TypeVar,
)

from typing_extensions import Concatenate, ParamSpec

from pipe_operator.python_flow.base import Pipe, PipeStart
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import (
    is_one_arg_lambda,
)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")


class Then(Generic[TInput, TOutput]):
    """
    Pipe-able element that allows the use of 1-arg lambda functions in the pipe.
    The lambda must take only 1 argument and can be typed explicitly if necessary.

    Args:
        f (Callable[[TInput], TOutput]): The function that will be called in the pipe.

    Raises:
        PipeError: If `f` is not a 1-arg lambda function.

    Examples:
        >>> (
        ...     PipeStart("1")
        ...     >> Then[str, int](lambda x: int(x) + 1)
        ...     >> Then(lambda x: x + 1)
        ...     >> PipeEnd()
        ... )
        3
    """

    __slots__ = ("f", "args", "kwargs", "is_tap", "is_thread")

    def __init__(self, f: Callable[[TInput], TOutput]) -> None:
        self.f = f
        self.args = ()
        self.kwargs = {}  # type: ignore
        self.is_tap = False
        self.is_thread = False
        self.check_f()

    def check_f(self) -> None:
        """f must be a 1-arg lambda function."""
        if not is_one_arg_lambda(self.f):
            raise PipeError(
                "`Then` only supports 1-arg lambda functions. Use `Pipe` instead."
            )

    def __rrshift__(self, other: PipeStart) -> PipeStart[TOutput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)


class Tap(Pipe[TInput, FuncParams, TInput]):
    """
    Pipe-able element that produces a side effect and returns the original value.
    Useful to perform async actions or to call an object's method that changes the state
    without returning anything.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], object]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Examples:
        >>> class BasicClass
        ...     def __init__(self, x: int) -> None:
        ...         self.x = x
        ...     def increment(self) -> None:
        ...         self.x += 1
        >>> (
        ...     PipeStart(1)
        ...     >> Pipe(BasicClass)
        ...     >> Tap(lambda x: x.increment())
        ...     >> Then(lambda x: x.x + 3)
        ...     >> Tap(lambda x: x + 100)
        ...     >> PipeEnd()
        ... )
        5
    """

    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        kwargs["_tap"] = True
        super().__init__(f, *args, **kwargs)  # type: ignore

    def __rrshift__(self, other: PipeStart) -> PipeStart[TInput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)
