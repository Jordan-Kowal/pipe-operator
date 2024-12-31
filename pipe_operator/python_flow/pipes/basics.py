from abc import ABC, abstractmethod
from typing import (
    Awaitable,
    Callable,
    Generic,
    TypeVar,
    Union,
    override,
)

from typing_extensions import Concatenate, ParamSpec

from pipe_operator.python_flow.base import PipeStart
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import (
    is_async_function,
    is_lambda,
    is_one_arg_lambda,
)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
FuncParams = ParamSpec("FuncParams")


class _Pipeable(ABC, Generic[TInput, FuncParams, TOutput]):
    __slots__ = ("f", "args", "kwargs")

    @abstractmethod
    def __init__(
        self,
        f: Callable[
            Concatenate[TInput, FuncParams], Union[TOutput, Awaitable[TOutput]]
        ],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None: ...

    @abstractmethod
    def validate_f(
        self,
        f: Callable[
            Concatenate[TInput, FuncParams], Union[TOutput, Awaitable[TOutput]]
        ],
    ) -> None: ...

    @abstractmethod
    def __rrshift__(
        self, other: PipeStart[TInput]
    ) -> Union[PipeStart[TInput], PipeStart[TOutput]]: ...


class _SyncPipeable(_Pipeable[TInput, FuncParams, TOutput]):
    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.validate_f(f)
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def validate_f(self, f: Callable) -> None:
        """f cannot be a lambda with multiple args nor an async function."""
        if is_lambda(f) and not is_one_arg_lambda(f):
            raise PipeError(
                "Lambda functions with more than 1 argument are not supported."
            )
        if is_async_function(f):
            raise PipeError(
                "`Pipe` does not support async functions. Use `AsyncPipe` instead."
            )


class _AsyncPipeable(_Pipeable[TInput, FuncParams, TOutput]):
    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.validate_f(f)
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def validate_f(self, f: Callable) -> None:
        """f must be an async function."""
        if not is_async_function(f):
            raise PipeError(
                "`AsyncPipe` only supports async functions. Use `Pipe` for regular functions."
            )


class Pipe(_SyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element for most already-defined functions/classes/methods.
    Functions should at least take 1 argument.
    When using a lambda, it can only take 1 argument.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], TOutput]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If `f` is a lambda with more than 1 arg.
        PipeError: If `f` is an async function.

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

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TOutput]:
        value: TOutput = self.f(other.value, *self.args, **self.kwargs)
        other.value = value  # type: ignore
        return other  # type: ignore


class Tap(_SyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element that produces a side effect and returns the original value.
    Useful to perform async actions or to call an object's method that changes the state
    without returning anything.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], TOutput]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If `f` is a lambda with more than 1 arg.
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

    @override
    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        self.f(other.value, *self.args, **self.kwargs)
        return other
