from typing import (
    Callable,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Concatenate, ParamSpec, TypeAlias

from pipe_operator.python_flow.base import PipeStart, _BasePipe
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import is_async_function

TInput = TypeVar("TInput")
FuncParams = ParamSpec("FuncParams")

ThreadId: TypeAlias = Union[str, int]


class ThreadPipe(_BasePipe[TInput, FuncParams, TInput]):
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

    Raises:
        PipeError: If `f` is an async function.

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

    __slots__ = _BasePipe.__slots__ + ("thread_id",)

    def __init__(
        self,
        thread_id: ThreadId,
        f: Callable[Concatenate[TInput, FuncParams], object],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.thread_id = thread_id
        super().__init__(f, *args, **kwargs)  # type: ignore

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        """Returns the unchanged PipeStart."""
        return other

    def validate_f(self) -> None:
        """f cannot be an async function."""
        if is_async_function(self.f):
            raise PipeError("`ThreadPipe` does not support async functions.`")


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

    def __rrshift__(self, other: PipeStart[TInput]) -> PipeStart[TInput]:
        """Returns the unchanged PipeStart."""
        return other
