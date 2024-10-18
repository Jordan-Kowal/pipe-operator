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
        if isinstance(other, PipeEnd):
            return self.value  # type: ignore
        self.result = other.f(self.value, *other.args, **other.kwargs)  # type: ignore
        if self.debug:
            self._print_debug(other.tap)
        if other.tap:
            return self  # type: ignore
        return PipeStart(self.result, debug=self.debug, chained=True)

    def _print_debug(self, is_tap: bool) -> None:
        # Extra print if first call
        if not self.chained:
            print(self.value)
        # Then print either the value or the result
        if is_tap:
            print(self.value)
        else:
            print(self.result)


class Pipe(Generic[TInput, FuncParams, TOutput]):
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
        self.raise_if_lambda()

    def raise_if_lambda(self) -> None:
        if is_lambda(self.f) and not self.tap:
            raise TypeError(
                "[pipe_operator] `Pipe` does not support lambda functions. Use `Then` instead."
            )


class PipeArgs(Generic[FuncParams, TOutput]):
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
    def __rrshift__(self, other: PipeStart[TValue]) -> TValue:
        # Never called, but needed for typechecking
        return other.value


class Then(Generic[TInput, TOutput]):
    def __init__(self, f: Callable[[TInput], TOutput]) -> None:
        self.f = f
        self.args = ()
        self.kwargs = {}  # type: ignore
        self.tap = False
        self.check_f()

    def check_f(self) -> None:
        if not is_one_arg_lambda(self.f):
            raise TypeError(
                "[pipe_operator] `Then` only supports 1-arg lambda functions. Use `Pipe` instead."
            )

    def __rrshift__(self, other: PipeStart) -> PipeStart[TOutput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)


class Tap(Pipe[TInput, FuncParams, TInput]):
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
