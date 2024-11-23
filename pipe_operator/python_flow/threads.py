from typing import (
    Callable,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.python_flow.base import Pipe, PipeStart

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
TValue = TypeVar("TValue")
FuncParams = ParamSpec("FuncParams")

ThreadId: TypeAlias = Union[str, int]


class ThreadPipe(Pipe[TInput, FuncParams, TInput]):
    """
    Pipe-able element that runs the given instructions in a separate thread.
    Much like `Tap`, it performs a side-effect and does not impact the original value.
    Useful for performing async/parallel actions.
    Can be used alongside `ThreadWait` to wait for specific/all threads to finish.

    Args:
        thread_id (str): A unique identifier (within this pipe) for the thread. Useful for `ThreadWait`.
        f (Callable[Concatenate[TInput, FuncParams], object]): The function that will be called in the thread.
        args (FuncParams.args): All args (except the first) that will be passed to the function `f`.
        kwargs (FuncParams.kwargs): All kwargs that will be passed to the function `f`.

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

    def __rrshift__(self, other: "PipeStart") -> PipeStart[TInput]:
        # Never called, but needed for typechecking
        return other.__rshift__(self)


class ThreadWait:
    """
    Pipe-able element used to wait for thread(s) (from `ThreadPipe`) to finish.

    Args:
        thread_ids (Optional[List[str]]): A list of thread identifiers to wait for. If not provided, all threads will be waited for.

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

    def __rrshift__(self, other: PipeStart[TValue]) -> PipeStart[TValue]:
        # Never called, but needed for typechecking
        return other
