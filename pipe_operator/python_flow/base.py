from threading import Thread
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import TypeAlias

from pipe_operator.shared.exceptions import PipeError

TValue = TypeVar("TValue")
TNewValue = TypeVar("TNewValue")

ThreadId: TypeAlias = Union[str, int]


class PipeEnd:
    """
    Pipe-able element to call as the last element in the pipe.
    During the `>>` operation, it will extract the value from the `PipeStart` and return it.

    Examples:
        >>> (PipeStart("1") >> Pipe(lambda x: int(x) + 1) >> PipeEnd())
        2
    """

    __slots__ = ()

    def __rrshift__(self, other: "PipeStart[TValue]") -> TValue:
        return other.value


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
