from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

ThenInput = TypeVar("ThenInput")
ThenOutput = TypeVar("ThenOutput")


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


class PipeValue(Generic[TValue]):
    def __init__(
        self, value: TValue, debug: bool = False, chained: bool = False
    ) -> None:
        self.value = value
        self.debug = debug
        self.result: Optional[Any] = None
        self.chained = chained

    def __rshift__(
        self, other: Union[Pipe[TValue, FuncParams, TOutput], "Then[TValue, TOutput]"]
    ) -> "PipeValue[TOutput]":
        self.result = other.f(self.value, *other.args, **other.kwargs)  # type: ignore
        is_tap = isinstance(other, Tap)
        if self.debug:
            self._print_debug(is_tap=is_tap)
        if is_tap:
            return self  # type: ignore
        return PipeValue(self.result, debug=self.debug, chained=True)

    def _print_debug(self, is_tap: bool) -> None:
        # Extra print if first call
        if not self.chained:
            print(self.value)
        # Then print either the value or the result
        if is_tap:
            print(self.value)
        else:
            print(self.result)


class Then(Generic[ThenInput, ThenOutput]):
    def __init__(self, f: Callable[[ThenInput], ThenOutput]) -> None:
        self.f = f
        self.args = ()
        self.kwargs = {}  # type: ignore


class Tap(Pipe[TValue, FuncParams, TValue]):
    def __init__(
        self,
        f: Callable[Concatenate[TValue, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        super().__init__(f, *args, **kwargs)  # type: ignore
