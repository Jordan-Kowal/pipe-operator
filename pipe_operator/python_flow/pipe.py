from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec

from pipe_operator.shared.utils import (
    function_needs_parameters,
    is_lambda,
    is_one_arg_lambda,
)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")


class PipeStart(Generic[TValue]):
    """
    The required starting point for the pipe workflow.
    It handles the `>>` operator to allow a fully working pipe workflow with
    various elements like `Pipe`, `PipeArgs`, `Then, `Tap`, and `PipeEnd`.

    Args:
        value (TValue): The starting value of the pipe.

    Examples:
        >>> def duplicate_string(x: str) -> str:
        ...     return f"{x}{x}"
        >>> def compute(x: int, y: int, z: int = 0) -> int:
        ...     return x + y + z
        >>> def _sum(*args: int) -> int:
        ...     return sum(args)
        >>> class BasicClass:
        ...     def __init__(self, value: int) -> None:
        ...         self.value = value
        ...
        ...     def increment(self) -> None:
        ...         self.value += 1
        ...
        ...     def get_value_method(self) -> int:
        ...         return self.value
        ...
        ...     @classmethod
        ...     def get_double(cls, instance: "BasicClass") -> "BasicClass":
        ...         return BasicClass(instance.value * 2)
        >>> (
        ...     PipeStart("3")
        ...     >> Pipe(duplicate_string)
        ...     >> Pipe(int)
        ...     >> Tap(compute, 2000, z=10)
        ...     >> Then(lambda x: x + 1)
        ...     >> Pipe(BasicClass)  # class
        ...     >> Pipe(BasicClass.get_double)
        ...     >> Tap(BasicClass.increment)
        ...     >> Pipe(BasicClass.get_value_method)
        ...     >> Then[int, int](lambda x: x * 2)
        ...     >> PipeArgs(_sum, 4, 5, 6)
        ...     >> PipeEnd()
        ... )
        153
    """

    def __init__(
        self, value: TValue, debug: bool = False, chained: bool = False
    ) -> None:
        self.value = value
        self.debug = debug
        self.result: Optional[Any] = None
        self.chained = chained

    def __rshift__(
        self, other: Union["Pipe[TValue, FuncParams, TOutput]", "Then[TValue, TOutput]"]
    ) -> "PipeStart[TOutput]":
        """
        Implements the `>>` operator to enable our pipe workflow.

        3 possible cases based on what `other` is:
            `Pipe/PipeArgs/Then`    -->     Classic pipe workflow where we return a new PipeStart with the result.
            `Tap`                   -->     Side effect where we call the function and a new PipeStart with the original value.
            `PipeEnd`               -->     Simply returns the raw value.

        Return can actually be of 3 types, also based on what `other` is:
            `Pipe/PipeArgs/Then`    -->     `PipeStart[TOutput]`
            `Tap`                   -->     `PipeStart[TValue]`
            `PipeEnd`               -->     `TValue`

        It is not indicated in the type annotations to avoid conflicts with type-checkers.
        """
        if isinstance(other, PipeEnd):
            return self.value  # type: ignore
        self.result = other.f(self.value, *other.args, **other.kwargs)  # type: ignore
        if self.debug:
            self._print_data(other.tap)
        if other.tap:
            return self  # type: ignore
        return PipeStart(self.result, debug=self.debug, chained=True)

    def _print_data(self, is_tap: bool) -> None:
        """Will either its value, its result, or both."""
        # Extra print if first call
        if not self.chained:
            print(self.value)
        # Then print either the value or the result
        if is_tap:
            print(self.value)
        else:
            print(self.result)


class Pipe(Generic[TInput, FuncParams, TOutput]):
    """
    Pipe-able element for most already-defined functions/classes/methods.
    Functions should at least take 1 argument.

    Note:
        Supports functions with no positional/keyword parameters, but `PipeArgs` should be preferred.
        Does not support lambdas, use `Then` instead.
        Does not support property calls, use `Then` with a custom lambda instead.

    Args:
        f (Callable[Concatenate[TInput, FuncParams], TOutput]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        TypeError: If `f` is a lambda function AND the tap flag is not set.

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
        ...     >> Pipe(compute, 30, z=10)
        ...     >> Pipe(BasicClass)
        ...     >> Then(lambda x: x.data + 3)
        ...     >> PipeEnd()
        ... )
        45
    """

    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.tap = bool(kwargs.pop("_tap", False))
        self.check_f()

    def check_f(self) -> None:
        """f must not be a lambda, except if it's a tap function."""
        if is_lambda(self.f) and not self.tap:
            raise TypeError(
                "[pipe_operator] `Pipe` does not support lambda functions. Use `Then` instead."
            )


class PipeArgs(Generic[FuncParams, TOutput]):
    """
    Pipe-able element for functions that takes no positional/keyword parameters.
    While `Pipe` would work, this one provides better type-checking.

    Args:
        f (Callable[FuncParams, TOutput]): The function that will be called in the pipe.
        args (FuncParams.args): All args that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        TypeError: If the `f` is a lambda function or if it has positional/keyword parameters.

    Examples:
        >>> def _sum(*args: int) -> int:
        ...     return sum(args)
        >>> (PipeStart(1) >> PipeArgs(_sum, 5, 10) >> PipeEnd())
        16
    """

    def __init__(
        self,
        f: Callable[FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.tap = bool(kwargs.pop("_tap", False))
        self.check_f()

    def check_f(self) -> None:
        """f must not be a lambda and have no position/keyword parameters."""
        if is_lambda(self.f) and not self.tap:
            raise TypeError(
                "[pipe_operator] `PipeArgs` does not support lambda functions. Use `Then` instead."
            )
        if function_needs_parameters(self.f):
            raise TypeError(
                "[pipe_operator] `PipeArgs` does not support functions with parameters. Use `Pipe` instead."
            )

    def __rrshift__(self, other: PipeStart) -> PipeStart[TOutput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)  # type: ignore


class PipeEnd:
    """
    Pipe-able element to call as the last element in the pipe.
    During the `>>` operation, it will extract the value from the `PipeStart` and return it.
    This allows us to receive the raw output rather than a `PipeStart` wrapper.

    Examples:
        >>> (PipeStart("1") >> Then(lambda x: int(x) + 1) >> PipeEnd())
        2
    """

    def __rrshift__(self, other: PipeStart[TValue]) -> TValue:
        # Never called, but needed for typechecking
        return other.value


class Then(Generic[TInput, TOutput]):
    """
    Pipe-able element that allows the use of 1-arg lambda functions in the pipe.
    The lambda must take only 1 argument and can be typed explicitly if necessary.

    Args:
        f (Callable[[TInput], TOutput]): The function that will be called in the pipe.

    Raises:
        TypeError: If `f` is not a 1-arg lambda function.

    Examples:
        >>> (
        ...     PipeStart("1")
        ...     >> Then[str, int](lambda x: int(x) + 1)
        ...     >> Then(lambda x: x + 1)
        ...     >> PipeEnd()
        ... )
        3
    """

    def __init__(self, f: Callable[[TInput], TOutput]) -> None:
        self.f = f
        self.args = ()
        self.kwargs = {}  # type: ignore
        self.tap = False
        self.check_f()

    def check_f(self) -> None:
        """f must be a 1-arg lambda function."""
        if not is_one_arg_lambda(self.f):
            raise TypeError(
                "[pipe_operator] `Then` only supports 1-arg lambda functions. Use `Pipe` instead."
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
