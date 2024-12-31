from threading import Thread
from typing import (
    Callable,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.python_flow.base import PipeStart
from pipe_operator.python_flow.pipes.basics import _SyncPipeable
from pipe_operator.shared.exceptions import PipeError

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")
TOutput = TypeVar("TOutput")

ThreadId: TypeAlias = Union[str, int]


class ThreadPipe(_SyncPipeable[TInput, FuncParams, TOutput]):
    """
    Pipe-able element that runs the given instructions in a separate thread.
    Much like `Tap`, it performs a side-effect and does not impact the original value.
    Can be used alongside `ThreadWait` to wait for specific/all threads to finish.

    Args:
        thread_id (str): A unique identifier (within this pipe) for the thread. Useful for `ThreadWait`.
        f (Callable[Concatenate[TInput, FuncParams], object]): The function that will be called in the thread.
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

    def __init__(
        self,
        thread_id: ThreadId,
        f: Callable[Concatenate[TInput, FuncParams], TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.thread_id = thread_id
        super().__init__(f, *args, **kwargs)

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        args = (other.value, *self.args)
        thread = Thread(target=self.f, args=args, kwargs=self.kwargs)  # type: ignore
        if self.thread_id in other.threads:
            raise PipeError(f"Thread ID {self.thread_id} already exists")
        other.threads[self.thread_id] = thread
        thread.start()
        return other


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

    def __init__(self, thread_ids: Optional[List[str]] = None) -> None:
        self.thread_ids = thread_ids

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        threads = other._get_threads(self.thread_ids)
        for thread in threads:
            thread.join()
        return other
