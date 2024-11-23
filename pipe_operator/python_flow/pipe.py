from threading import Thread
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeAlias,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec

from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import (
    function_needs_parameters,
    is_lambda,
    is_one_arg_lambda,
)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

ThreadId: TypeAlias = Union[str, int]


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

        3 possible cases based on what `other` is:
            `Pipe/PipeArgs/Then`    -->     Classic pipe workflow where we return the updated PipeStart with the result.
            `Tap`                   -->     Side effect where we call the function and return the unchanged PipeStart.
            `PipeEnd`               -->     Simply returns the raw value.

        Return can actually be of 3 types, also based on what `other` is:
            `Pipe/PipeArgs/Then`    -->     `PipeStart[TOutput]`
            `Tap`                   -->     `PipeStart[TValue]`
            `PipeEnd`               -->     `TValue`

        It is not indicated in the type annotations to avoid conflicts with type-checkers.
        """
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


class ThreadPipe(Pipe[TInput, FuncParams, TInput]):
    """
    Pipe-able element that runs the given instructions in a separate thread.
    Much like `Tap`, it performs a side-effect and does not impact the original value.
    Useful for performing async/parallel actions.

    Can be used alongside `ThreadWait` to wait for specific/all threads to finish.

    Args:
        thread_id (str): A unique identifier (within this pipe) for the thread.
        f (Callable[Concatenate[TInput, FuncParams], object]): The function that will be called in the pipe.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Examples:
        >>> (
        ...     PipeStart(3)
        ...     >> ThreadPipe("t1", lambda _: time.sleep(0.1))
        ...     >> ThreadWait(["t1"])
        ...     >> PipeEnd()
        ... )
        3
    """

    __slots__ = Pipe.__slots__ + ("thread_id",)

    def __init__(
        self,
        thread_id: ThreadId,
        f: Callable[Concatenate[TInput, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.thread_id = thread_id
        kwargs["_thread"] = True
        super().__init__(f, *args, **kwargs)  # type: ignore

    def __rrshift__(self, other: PipeStart) -> PipeStart[TInput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)


class ThreadWait:
    """
    Pipe-able element used to wait for thread(s) (from `ThreadPipe`) to finish.

    Args:
        thread_ids (Optional[List[str]]): A list of thread identifiers to wait for. If not provided, all threads will be waited for.

    Examples:
        >>> (
        ...     PipeStart(3)
        ...     >> ThreadPipe("t1", lambda _: time.sleep(0.1))
        ...     >> ThreadWait(["t1"])
        ...     >> PipeEnd()
        ... )
        3
    """

    __slots__ = ("thread_ids",)

    def __init__(self, thread_ids: Optional[List[str]] = None) -> None:
        self.thread_ids = thread_ids

    def __rrshift__(self, other: PipeStart[TValue]) -> PipeStart[TValue]:
        # Never called, but needed for typechecking
        return other
