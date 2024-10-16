from typing import Any, Callable, Concatenate, Generic, Optional, ParamSpec, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")


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


class PipeStart(Generic[TValue]):
    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.result: Optional[Any] = None
        self.chained = False

    def __rshift__(
        self, other: Pipe[TValue, FuncParams, TOutput]
    ) -> "_PipeChain[TOutput]":
        self.result = other.f(self.value, *other.args, **other.kwargs)
        is_tap = isinstance(other, Tap)
        if self.debug:
            self._print_debug(is_tap=is_tap)
        if is_tap:
            return self  # type: ignore
        return _PipeChain(self.result, debug=self.debug)

    def _print_debug(self, is_tap: bool) -> None:
        # Extra print if first call
        if not self.chained:
            print(self.value)
        # Then print either the value or the result
        if is_tap:
            print(self.value)
        else:
            print(self.result)


class _PipeChain(PipeStart[TValue]):
    def __init__(self, value: TValue, debug: bool = False) -> None:
        super().__init__(value, debug)
        self.chained = True


class Tap(Pipe[TValue, FuncParams, TValue]):
    def __init__(
        self,
        f: Callable[Concatenate[TValue, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        super().__init__(f, *args, **kwargs)  # type: ignore
