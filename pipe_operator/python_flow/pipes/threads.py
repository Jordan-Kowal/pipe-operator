from typing import (
    Callable,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.python_flow.pipes.basics import Pipe

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")
TOutput = TypeVar("TOutput")

ThreadId: TypeAlias = Union[str, int]


class ThreadPipe(Pipe[TInput, FuncParams, TOutput]):
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

    __slots__ = Pipe.__slots__ + ("thread_id",)

    def __init__(
        self,
        thread_id: ThreadId,
        f: Callable[Concatenate[TInput, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.thread_id = thread_id
        super().__init__(f, *args, **kwargs)  # type: ignore


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
