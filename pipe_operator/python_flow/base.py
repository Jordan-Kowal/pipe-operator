import asyncio
from threading import Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import ParamSpec, TypeAlias

from pipe_operator.shared.exceptions import PipeError

if TYPE_CHECKING:
    from pipe_operator.python_flow.pipes.asynchronous import AsyncPipe
    from pipe_operator.python_flow.pipes.basics import Pipe, Tap
    from pipe_operator.python_flow.pipes.threads import ThreadPipe, ThreadWait


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

ThreadId: TypeAlias = Union[str, int]


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

    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.history: List[Any] = []
        self.result: Optional[Any] = None
        self.threads: Dict[ThreadId, Thread] = {}
        if self.debug:
            print(self.value)
            self.history.append(value)

    @overload
    def __rshift__(
        self, other: "Tap[TValue, FuncParams, TOutput]"
    ) -> "PipeStart[TValue]": ...

    @overload
    def __rshift__(
        self, other: "ThreadPipe[TValue, FuncParams, TOutput]"
    ) -> "PipeStart[TValue]": ...

    @overload
    def __rshift__(
        self, other: "AsyncPipe[TValue, FuncParams, TOutput]"
    ) -> "PipeStart[TOutput]": ...

    @overload
    def __rshift__(
        self, other: "Pipe[TValue, FuncParams, TOutput]"
    ) -> "PipeStart[TOutput]": ...

    @overload
    def __rshift__(self, other: "ThreadWait") -> "PipeStart[TValue]": ...

    @overload
    def __rshift__(self, other: "PipeEnd") -> "TValue": ...

    def __rshift__(
        self,
        other: Union[
            "Tap[TValue, FuncParams, TOutput]",
            "ThreadPipe[TValue, FuncParams, TOutput]",
            "AsyncPipe[TValue, FuncParams, TOutput]",
            "Pipe[TValue, FuncParams, TOutput]",
            "ThreadWait",
            "PipeEnd",
        ],
    ) -> Union["PipeStart[TValue]", "PipeStart[TOutput]", "TValue"]:
        """
        Implements the `>>` operator to enable our pipe workflow.

        Multiple possible cases based on what `other` is:
            `Pipe/AsyncPipe`                -->     Classic pipe workflow where we return the updated PipeStart with the result.
            `Tap/ThreadPipe`                -->     Side effect where we call the function and return the unchanged PipeStart.
            `ThreadWait`                    -->     Blocks the pipe until some threads finish.
            `PipeEnd`                       -->     Simply returns the raw value.
        """
        from pipe_operator.python_flow.pipes.asynchronous import AsyncPipe
        from pipe_operator.python_flow.pipes.basics import Tap
        from pipe_operator.python_flow.pipes.threads import ThreadPipe, ThreadWait

        # ====> [EXIT] PipeEnd: returns the raw value
        if isinstance(other, PipeEnd):
            return self.value

        # ====> [EXIT] ThreadWait: waits for some threads to finish, then returns the value
        if isinstance(other, ThreadWait):
            threads = self._get_threads(other.thread_ids)
            for thread in threads:
                thread.join()
            return self

        # ====> [EXIT] ThreadPipe: calls the function in a separate thread
        if isinstance(other, ThreadPipe):
            args = (self.value, *other.args)  # type: ignore
            thread = Thread(target=other.f, args=args, kwargs=other.kwargs)  # type: ignore
            if other.thread_id in self.threads:
                raise PipeError(f"Thread ID {other.thread_id} already exists")
            self.threads[other.thread_id] = thread
            thread.start()
            self._handle_debug()
            return self

        # ====> Executes the instructions
        if isinstance(other, AsyncPipe):
            self.result = asyncio.run(other.f(self.value, *other.args, **other.kwargs))  # type: ignore
        else:
            self.result = other.f(self.value, *other.args, **other.kwargs)

        # ====> [EXIT] Tap: returns unchanged PipeStart
        if isinstance(other, Tap):
            self.result = None
            self._handle_debug()
            return self

        # ====> [EXIT] Otherwise, returns the updated PipeStart
        self.value, self.result = self.result, None
        self._handle_debug()
        return self

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


class PipeEnd:
    """
    Pipe-able element to call as the last element in the pipe.
    During the `>>` operation, it will extract the value from the `PipeStart` and return it.

    Examples:
        >>> (PipeStart("1") >> Pipe(lambda x: int(x) + 1) >> PipeEnd())
        2
    """

    __slots__ = ()
