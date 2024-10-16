from typing import Callable, Concatenate, Generic, ParamSpec, TypeVar

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


class PipeValue(Generic[TValue]):
    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug

    def __rshift__(
        self, other: Pipe[TValue, FuncParams, TOutput]
    ) -> "PipeValue[TOutput]":
        result = other.f(self.value, *other.args, **other.kwargs)
        if self.debug:
            print(result)
        return PipeValue(result)
