from abc import ABC, abstractmethod
from typing import (
    Callable,
    Generic,
    TypeVar,
)

from typing_extensions import Concatenate, ParamSpec

from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import (
    is_async_function,
    is_lambda,
    is_one_arg_lambda,
)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
FuncParams = ParamSpec("FuncParams")


class _BasePipe(ABC, Generic[TInput, FuncParams, TOutput]):
    """Base class for pipe-able elements."""

    __slots__ = ("f", "args", "kwargs")

    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.validate_f()

    @abstractmethod
    def validate_f(self) -> None:
        """Implements validation for the `f` function."""


class Pipe(_BasePipe[TInput, FuncParams, TOutput]):
    """
    Pipe-able element for most already-defined functions/classes/methods.
    Functions should at least take 1 argument.
    When using a lambda, it can only take 1 argument.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], TOutput]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If `f` is a lambda with more than 1 arg or an async function.

    Examples:
        >>> class BasicClass:
        ...     def __init__(self, data: int) -> None:
        ...         self.data = data
        >>> def double(x: int) -> int:
        ...     return x * 2
        >>> def compute(x: int, y: int, z: int = 0) -> int:
        ...     return x + y + z
        >>> (
        ...     PipeStart(1)
        ...     >> Pipe(double)
        ...     >> Pipe(lambda x: x + 1)
        ...     >> Pipe(compute, 30, z=10)
        ...     >> Pipe(BasicClass)
        ...     >> Pipe[BasicClass, [], int](lambda x: x.data)
        ...     >> PipeEnd()
        ... )
        43
    """

    def validate_f(self) -> None:
        """f cannot be a lambda with multiple args nor an async function."""
        if is_lambda(self.f) and not is_one_arg_lambda(self.f):
            raise PipeError(
                "Lambda functions with more than 1 argument are not supported."
            )
        if is_async_function(self.f):
            raise PipeError(
                "`Pipe` does not support async functions. Use `AsyncPipe` instead."
            )


class Tap(_BasePipe[TInput, FuncParams, TInput]):
    """
    Pipe-able element that produces a side effect and returns the original value.
    Useful to perform async actions or to call an object's method that changes the state
    without returning anything.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], object]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If `f` is an async function.

    Examples:
        >>> class BasicClass
        ...     def __init__(self, x: int) -> None:
        ...         self.x = x
        >>> (
        ...     PipeStart(1)
        ...     >> Pipe(BasicClass)
        ...     >> Tap(lambda x: print(x))
        ...     >> Pipe[BasicClass, [], int](lambda x: x.x + 3)
        ...     >> Tap(lambda x: x + 100)
        ...     >> PipeEnd()
        ... )
        4
    """

    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        super().__init__(f, *args, **kwargs)  # type: ignore

    def validate_f(self) -> None:
        """f cannot be a lambda with multiple args nor an async function."""
        if is_lambda(self.f) and not is_one_arg_lambda(self.f):
            raise PipeError(
                "Lambda functions with more than 1 argument are not supported."
            )
        if is_async_function(self.f):
            raise PipeError(
                "`Pipe` does not support async functions. Use `AsyncPipe` instead."
            )
