from threading import Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import (
    function_needs_parameters,
    is_lambda,
)

if TYPE_CHECKING:
    from pipe_operator.python_flow.extras import Then


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

ThreadId: TypeAlias = Union[str, int]


class PipeStart(Generic[TValue]):
    """
    The required starting point for the pipe workflow.
    It handles the `>>` operator to allow a fully working pipe workflow with
    various elements like: `Pipe`, `PipeArgs`, `Then, `Tap`, `ThreadPipe`, `ThreadWait`, and `PipeEnd`.

    Args:
        value (TValue): The starting value of the pipe.

    Examples:
        >>> import time
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
        ...     >> ThreadPipe("t1", lambda _: time.sleep(0.2))
        ...     >> Pipe(int)
        ...     >> ThreadPipe("t2", double)
        ...     >> Tap(compute, 2000, z=10)
        ...     >> Then(lambda x: x + 1)
        ...     >> Pipe(BasicClass)  # class
        ...     >> Pipe(BasicClass.get_double)
        ...     >> Tap(BasicClass.increment)
        ...     >> Pipe(BasicClass.get_value_method)
        ...     >> Then[int, int](lambda x: x * 2)
        ...     >> ThreadPipe("t1", lambda _: time.sleep(0.1))
        ...     >> ThreadWait(["t1"])
        ...     >> PipeArgs(_sum, 4, 5, 6)
        ...     >> ThreadWait()
        ...     >> PipeEnd()
        ... )
        153
    """

    __slots__ = ("value", "debug", "result", "history", "threads")

    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.history: List[Any] = []
        self.result: Optional[Any] = None
        self.threads: Dict[ThreadId, Thread] = {}
        if self.debug:
            print(self.value)
            self.history.append(value)

    def __rshift__(
        self, other: Union["Pipe[TValue, FuncParams, TOutput]", "Then[TValue, TOutput]"]
    ) -> "PipeStart[TOutput]":
        """
        Implements the `>>` operator to enable our pipe workflow.

        Multiple possible cases based on what `other` is:
            `Pipe/PipeArgs/Then`            -->     Classic pipe workflow where we return the updated PipeStart with the result.
            `Tap`                           -->     Side effect where we call the function and return the unchanged PipeStart.
            `ThreadPipe`                    -->     Like `Tap`, but in a separate thread.
            `ThreadWait`                    -->     Blocks the pipe until some threads finish.
            `PipeEnd`                       -->     Simply returns the raw value.

        Return can actually be of 3 types, also based on what `other` is:
            `Pipe/PipeArgs/Then`            -->     `PipeStart[TOutput]`
            `Tap/ThreadPipe/ThreadWait`     -->     `PipeStart[TValue]`
            `PipeEnd`                       -->     `TValue`

        It is not indicated in the type annotations to avoid conflicts with type-checkers.
        """
        from pipe_operator.python_flow.threads import ThreadPipe, ThreadWait

        # ====> [EXIT] PipeEnd: returns the raw value
        if isinstance(other, PipeEnd):
            return self.value  # type: ignore

        # ====> [EXIT] ThreadWait: waits for some threads to finish, then returns the value
        if isinstance(other, ThreadWait):
            threads = self._get_threads(other.thread_ids)
            for thread in threads:
                thread.join()
            return self  # type: ignore

        # ====> [EXIT] ThreadPipe: calls the function in a separate thread
        if isinstance(other, ThreadPipe):
            args = (self.value, *other.args)
            thread = Thread(target=other.f, args=args, kwargs=other.kwargs)
            if other.thread_id in self.threads:
                raise PipeError(f"Thread ID {other.thread_id} already exists")
            self.threads[other.thread_id] = thread
            thread.start()
            self._handle_debug()
            return self  # type: ignore

        # ====> Executes the instruction asynchronously
        self.result = other.f(self.value, *other.args, **other.kwargs)  # type: ignore

        # ====> [EXIT] Tap: returns unchanged PipeStart
        if other.is_tap:
            self.result = None
            self._handle_debug()
            return self  # type: ignore

        # ====> [EXIT] Otherwise, returns the updated PipeStart
        self.value, self.result = self.result, None  # type: ignore
        self._handle_debug()
        return self  # type: ignore

    def _handle_debug(self) -> None:
        """Will print and append to history. Debug mode only."""
        if not self.debug:
            return
        print(self.value)
        self.history.append(self.value)

    def _get_threads(self, thread_ids: Optional[List[str]] = None) -> List[Thread]:
        """Returns a list of threads, filtered by thread_ids if provided."""
        if thread_ids is None:
            return list(self.threads.values())
        for thread_id in thread_ids:
            if thread_id not in self.threads:
                raise PipeError(f"Unknown thread_id: {thread_id}")
        return [self.threads[tid] for tid in thread_ids]


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
        PipeError: If `f` is a lambda function AND it is neither a `tap` nor a `thread`.

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

    __slots__ = ("f", "args", "kwargs", "is_tap", "is_thread")

    def __init__(
        self,
        f: Callable[Concatenate[TInput, FuncParams], TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.is_tap = bool(kwargs.pop("_tap", False))
        self.is_thread = bool(kwargs.pop("_thread", False))
        self.check_f()

    def check_f(self) -> None:
        """f must not be a lambda, except if it's a is_tap or is_thread function."""
        if is_lambda(self.f) and not (self.is_tap or self.is_thread):
            raise PipeError(
                "`Pipe` does not support lambda functions except in 'tap' or 'thread' mode. Use `Then` instead."
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
        PipeError: If the `f` is a lambda function (and is not a tap or thread) or if it has positional/keyword parameters.

    Examples:
        >>> def _sum(*args: int) -> int:
        ...     return sum(args)
        >>> (PipeStart(1) >> PipeArgs(_sum, 5, 10) >> PipeEnd())
        16
    """

    __slots__ = ("f", "args", "kwargs", "is_tap", "is_thread")

    def __init__(
        self,
        f: Callable[FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.is_tap = bool(kwargs.pop("_tap", False))
        self.is_thread = bool(kwargs.pop("_thread", False))
        self.check_f()

    def check_f(self) -> None:
        """f must not be a lambda and have no position/keyword parameters."""
        if is_lambda(self.f) and not (self.is_tap or self.is_thread):
            raise PipeError(
                "`PipeArgs` does not support lambda functions except in 'tap' or 'thread' mode. Use `Then` instead."
            )
        if function_needs_parameters(self.f):
            raise PipeError(
                "`PipeArgs` does not support functions with parameters. Use `Pipe` instead."
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

    __slots__ = ()

    def __rrshift__(self, other: PipeStart[TValue]) -> TValue:
        # Never called, but needed for typechecking
        return other.value
