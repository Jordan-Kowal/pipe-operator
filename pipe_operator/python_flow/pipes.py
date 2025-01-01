from abc import ABC, abstractmethod
import asyncio
from threading import Thread
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Self,
    TypeVar,
    Union,
    final,
    override,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import (
    is_async_function,
    is_lambda,
    is_one_arg_lambda,
)

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")
TOutput = TypeVar("TOutput")

SyncCallable: TypeAlias = Callable[Concatenate[TInput, FuncParams], TOutput]
AsyncCallable: TypeAlias = Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]]
PipeableCallable: TypeAlias = Union[
    Callable[Concatenate[TInput, FuncParams], TOutput],
    Callable[Concatenate[TInput, FuncParams], Awaitable[TOutput]],
]

TValue = TypeVar("TValue")
TNewValue = TypeVar("TNewValue")

ThreadId: TypeAlias = Union[str, int]


# region PipeStart
class PipeStart(Generic[TValue]):
    """
    The required starting point for the pipe workflow.
    It handles the `>>` operator to allow a fully working pipe workflow with
    various elements like: `Pipe`, `AsyncPipe`, `Tap`, `ThreadPipe`, `ThreadWait`, and `PipeEnd`.

    Args:
        value (TValue): The starting value of the pipe.

    Examples:
        >>> import time
        >>> import asyncio
        >>> async def async_add_one(value: int) -> int:
        ...     await asyncio.sleep(0.1)
        ...     return value + 1
        >>> def duplicate_string(x: str) -> str:
        ...     return f"{x}{x}"
        >>> def double(x: int) -> int:
        ...     return x * 2
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
        ...     >> AsyncPipe(async_add_one)
        ...     >> ThreadPipe("t2", double)
        ...     >> Tap(compute, 2000, z=10)
        ...     >> Pipe(lambda x: x + 1)
        ...     >> Pipe(BasicClass)
        ...     >> Pipe(BasicClass.get_double)
        ...     >> Tap(BasicClass.increment)
        ...     >> Pipe(BasicClass.get_value_method)
        ...     >> Pipe[int, [], int](lambda x: _sum(x, 4, 5, 6))
        ...     >> ThreadWait()
        ...     >> PipeEnd()
        ... )
        86
    """

    __slots__ = ("value", "debug", "result", "history", "threads")

    @final
    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.history: List[Any] = []
        self.result: Optional[Any] = None
        self.threads: Dict[ThreadId, Thread] = {}
        self._handle_debug()

    @classmethod
    @final
    def update(
        cls, pipe_start: "PipeStart[TValue]", value: TNewValue
    ) -> "PipeStart[TNewValue]":
        pipe_start.value = value  # type: ignore
        pipe_start._handle_debug()
        return pipe_start  # type: ignore

    @final
    def keep(self) -> Self:
        self._handle_debug()
        return self

    @final
    def _handle_debug(self) -> None:
        """Will print and append to history. Debug mode only."""
        if not self.debug:
            return
        print(self.value)
        self.history.append(self.value)

    @final
    def _get_threads(self, thread_ids: Optional[List[str]] = None) -> List[Thread]:
        """Returns a list of threads, filtered by thread_ids if provided."""
        if thread_ids is None:
            return list(self.threads.values())
        for thread_id in thread_ids:
            if thread_id not in self.threads:
                raise PipeError(f"Unknown thread_id: {thread_id}")
        return [self.threads[tid] for tid in thread_ids]


# region _Pipeable
class _Pipeable(ABC, Generic[TInput, FuncParams, TOutput]):
    __slots__ = ("f", "args", "kwargs")

    @abstractmethod
    def __init__(
        self,
        f: PipeableCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None: ...

    @abstractmethod
    def validate_f(
        self,
        f: PipeableCallable[TInput, FuncParams, TOutput],
    ) -> None: ...

    @abstractmethod
    def __rrshift__(
        self, other: PipeStart[TInput]
    ) -> Union[PipeStart[TInput], PipeStart[TOutput]]: ...


# region _SyncPipeable
class _SyncPipeable(_Pipeable[TInput, FuncParams, TOutput]):
    @override
    def __init__(
        self,
        f: SyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.validate_f(f)
        self.f = f
        self.args = args
        self.kwargs = kwargs

    @override
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


# region _AsyncPipeable
class _AsyncPipeable(_Pipeable[TInput, FuncParams, TOutput]):
    @override
    def __init__(
        self,
        f: AsyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.validate_f(f)
        self.f = f
        self.args = args
        self.kwargs = kwargs

    @override
    def validate_f(self, f: Callable) -> None:
        """f must be an async function."""
        if not is_async_function(f):
            raise PipeError(
                "`AsyncPipe` only supports async functions. Use `Pipe` for regular functions."
            )


# region Pipe
class Pipe(_SyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element for most already-defined functions/classes/methods.
    Functions should at least take 1 argument.
    When using a lambda, it can only take 1 argument.

    Args:
        f (SyncCallable[TInput, FuncParams, TOutput]): The function that will be called in the pipe.
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

    @override
    @final
    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TOutput]:
        value: TOutput = self.f(other.value, *self.args, **self.kwargs)
        return PipeStart.update(other, value)


# region Tap
class Tap(_SyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element that produces a side effect and returns the original value.
    Useful to perform async actions or to call an object's method that changes the state
    without returning anything.

    Args:
        f (SyncCallable[TInput, FuncParams, TOutput]): The function that will be called in the pipe.
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
    @final
    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        self.f(other.value, *self.args, **self.kwargs)
        return other.keep()


# region AsyncPipe
class AsyncPipe(_AsyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element to run and wait for async functions (through asyncio).
    Similar to the regular `Pipe` but for async functions.

    Args:
        f (AsyncCallable[TInput, FuncParams, TOutput]): The async function that will be called with asyncio.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If the `f` is not an async function.

    Examples:
        >>> import asyncio
        >>> async def add_one(value: int) -> int:
        ...     await asyncio.sleep(0.1)
        ...     return value + 1
        >>> PipeStart(3) >> AsyncPipe(add_one) >> PipeEnd()
        4
    """

    @override
    @final
    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TOutput]:
        value = asyncio.run(self.f(other.value, *self.args, **self.kwargs))  # type: ignore
        return PipeStart.update(other, value)


# region ThreadPipe
class ThreadPipe(_SyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element that runs the given instructions in a separate thread.
    Much like `Tap`, it performs a side-effect and does not impact the original value.
    Can be used alongside `ThreadWait` to wait for specific/all threads to finish.

    Args:
        thread_id (str): A unique identifier (within this pipe) for the thread. Useful for `ThreadWait`.
        f (SyncCallable[TInput, FuncParams, TOutput]): The function that will be called in the thread.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

    Raises:
        PipeError: If `f` is a lambda with more than 1 arg.
        PipeError: If `f` is an async function.
        PipeError: If `thread_id` is already used in the ongoing pipe.

    Examples:
        >>> import time
        >>> (
        ...     PipeStart(3)
        ...     >> ThreadPipe("t1", lambda _: time.sleep(0.1))
        ...     >> ThreadWait(["t1"])
        ...     >> PipeEnd()
        ... )
        3
    """

    __slots__ = _SyncPipeable.__slots__ + ("thread_id",)

    @override
    @final
    def __init__(
        self,
        thread_id: ThreadId,
        f: SyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.thread_id = thread_id
        super().__init__(f, *args, **kwargs)

    @override
    @final
    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        args = (other.value, *self.args)
        thread = Thread(target=self.f, args=args, kwargs=self.kwargs)  # type: ignore
        if self.thread_id in other.threads:
            raise PipeError(f"Thread ID {self.thread_id} already exists")
        other.threads[self.thread_id] = thread
        thread.start()
        return other.keep()


# region ThreadWait
class ThreadWait:
    """
    Pipe-able element used to wait for thread(s) (from `ThreadPipe`) to finish.

    Args:
        thread_ids (Optional[List[str]]): A list of thread identifiers to wait for. If not provided, all threads will be waited for.

    Raises:
        PipeError: If `thread_ids` has unknown values.

    Examples:
        >>> import time
        >>> (
        ...     PipeStart(3)
        ...     >> ThreadPipe("t1", lambda _: time.sleep(0.1))
        ...     >> ThreadWait(["t1"])
        ...     >> PipeEnd()
        ... )
        3
    """

    __slots__ = ("thread_ids",)

    @final
    def __init__(self, thread_ids: Optional[List[str]] = None) -> None:
        self.thread_ids = thread_ids

    @final
    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        threads = other._get_threads(self.thread_ids)
        for thread in threads:
            thread.join()
        return other.keep()


# region PipeEnd
class PipeEnd:
    """
    Pipe-able element to call as the last element in the pipe.
    During the `>>` operation, it will extract the value from the `PipeStart` and return it.

    Examples:
        >>> (PipeStart("1") >> Pipe(lambda x: int(x) + 1) >> PipeEnd())
        2
    """

    __slots__ = ()

    @final
    def __rrshift__(self, other: PipeStart[TValue]) -> TValue:
        return other.value
