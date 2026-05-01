import asyncio
from threading import Thread
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    cast,
    overload,
)

from typing_extensions import Self

from pipe_operator.python_flow.types import (
    AsyncCallable,
    FuncParams,
    PipeableCallable,
    SyncCallable,
    TaskId,
    TInput,
    TNewValue,
    TOutput,
    TValue,
)
from pipe_operator.python_flow.utils import is_async_pipeable, is_sync_pipeable
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import is_lambda, is_one_arg_lambda


# region PipeObject
class PipeObject(Generic[TValue]):
    """
    The starting point of the pipe, which gets passed down at every step/

    Args:
        value (TValue): The value to start with.
        debug (Optional[bool]): Whether to run in debug mode, which prints the value at every step.

    Example:
        >>> start(1) >> pipe(add_one) >> then[int, int](lambda x: x * 2) >> end()
        4
    """

    __slots__ = ("value", "debug", "history", "tasks")

    value: Any
    debug: bool
    history: List[Any]
    tasks: Dict[TaskId, Thread]

    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.history = []
        self.tasks = {}
        self._handle_debug()

    def update(self, value: TNewValue) -> "PipeObject[TNewValue]":
        """Updates the value of the PipeObject and returns the object."""
        self.value = value
        self._handle_debug()
        return cast("PipeObject[TNewValue]", self)

    def retain(self) -> Self:
        """Returns the PipeObject with its value unchanged."""
        self._handle_debug()
        return self

    def register_thread(self, task_id: TaskId, thread: Thread) -> None:
        """Stores the thread in the tasks dictionary and starts it."""
        if task_id in self.tasks:
            raise PipeError(f"Task ID {task_id} already exists")
        self.tasks[task_id] = thread
        thread.start()

    def wait_for_tasks(self, task_ids: Optional[List[TaskId]] = None) -> None:
        """Explicitly waits for the given tasks to complete."""
        threads = self._get_tasks(task_ids)
        for thread in threads:
            thread.join()

    def _handle_debug(self) -> None:
        """Will print and append to history. Debug mode only."""
        if not self.debug:
            return
        print(self.value)
        self.history.append(self.value)

    def _get_tasks(self, task_ids: Optional[List[TaskId]] = None) -> List[Thread]:
        """Returns a list of tasks, filtered by task_ids if provided."""
        if task_ids is None:
            return list(self.tasks.values())
        for task_id in task_ids:
            if task_id not in self.tasks:
                raise PipeError(f"Unknown task_id: {task_id}")
        return [self.tasks[tid] for tid in task_ids]


# region Pipe
class Pipe(Generic[TInput, FuncParams, TOutput]):
    __slots__ = ("f", "args", "kwargs")

    f: SyncCallable[TInput, FuncParams, TOutput]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __init__(
        self,
        f: SyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TOutput]:
        """Runs the function and updates the PipeObject."""
        result = self.f(other.value, *self.args, **self.kwargs)
        return other.update(result)


# region AsyncPipe
class AsyncPipe(Generic[TInput, FuncParams, TOutput]):
    __slots__ = ("f", "args", "kwargs")

    f: AsyncCallable[TInput, FuncParams, TOutput]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __init__(
        self,
        f: AsyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TOutput]:
        """Runs the function and updates the PipeObject."""
        coro = self.f(other.value, *self.args, **self.kwargs)
        value = asyncio.run(coro)
        return other.update(value)


# region pipe (factory)
# Async overload comes first so async functions resolve to `AsyncPipe`.
# Mypy flags this as overlapping with the sync overload because a sync function
# could in theory return a Coroutine. Runtime dispatch handles this correctly.
@overload
def pipe(  # type: ignore[overload-overlap]
    f: AsyncCallable[TInput, FuncParams, TOutput],
    *args: FuncParams.args,
    **kwargs: FuncParams.kwargs,
) -> AsyncPipe[TInput, FuncParams, TOutput]: ...


@overload
def pipe(
    f: SyncCallable[TInput, FuncParams, TOutput],
    *args: FuncParams.args,
    **kwargs: FuncParams.kwargs,
) -> Pipe[TInput, FuncParams, TOutput]: ...


# Fallback overload for variadic callables (e.g. `def f(*args): ...`).
# Pyrefly's strict reading of `Concatenate[T, P]` rejects matching against `*args`,
# so this catches that case. Loses arg-checking for variadic case but real-world usage works.
@overload
def pipe(
    f: Callable[..., TOutput],
    *args: Any,
    **kwargs: Any,
) -> Pipe[Any, Any, TOutput]: ...


def pipe(
    f: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Most common pipeable that can be used for sync/async functions, classes, methods, etc.
    Function should take at least 1 argument and cannot be lambdas (use `then` for that).

    Args:
        f (PipeableCallable[TInput, FuncParams, TOutput]): Function to run.
        args (FuncParams.args): The args (except the first) to pass to the function.
        kwargs (FuncParams.kwargs): The kwargs to pass to the function.

    Example:
        >>> (
        ...     start("3")
        ...     >> pipe(int)  # function
        ...     >> pipe(async_add_one)  # async function
        ...     >> pipe(func_with_args, arg1, arg2=arg2)  # function with args/kwargs
        ...     >> pipe(custom_sum, 5)  # function with no positional args
        ...     >> pipe(BasicClass)  # class
        ...     >> pipe(BasicClass.my_classmethod)  # classmethod
        ...     >> pipe(BasicClass.my_method_with_args, 5)  # method with arg
        ...     >> end()
        ... )
        9
    """
    if is_lambda(f):
        raise PipeError("`pipe` does not support lambda functions. Use `then` instead.")
    if is_async_pipeable(f):
        return AsyncPipe(f, *args, **kwargs)
    if is_sync_pipeable(f):
        return Pipe(f, *args, **kwargs)
    raise PipeError("Unsupported function provided to `pipe`.")


# region Then
class Then(Generic[TInput, TOutput]):
    """
    Pipeable for 1-arg lambda functions.
    Similar to elixir's `then`.
    Useful for one-liners and attribute extraction.

    Args:
        f (Callable[[TInput], TOutput]): Function to run. Must be a one-arg lambda.

    Example:
        >>> (
        ...     start(3)
        ...     >> then[int, int](lambda x: x + 1)
        ...     >> then[int, str](lambda x: str(x))
        ...     >> end()
        ... )
        "4"
    """

    __slots__ = ("f",)

    f: Callable[[TInput], TOutput]

    def __init__(self, f: Callable[[TInput], TOutput]) -> None:
        if not is_one_arg_lambda(f):
            raise PipeError("`then` only supports one-arg lambdas. Try `pipe` instead.")
        self.f = f

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TOutput]:
        """Updates the PipeObject with the result of the function call."""
        value = self.f(other.value)
        return other.update(value)


# region Tap
class Tap(Generic[TInput, FuncParams]):
    """
    Pipeable that runs the function but returns the original value.
    Similar to elixir's `tap`.
    Useful to trigger side-effects without breaking the pipe chain.

    Args:
        f (PipeableCallable[TInput, FuncParams, Any]): Function to run.
        args (FuncParams.args): The args (except the first) to pass to the function.
        kwargs (FuncParams.kwargs): The kwargs to pass to the function.

    Example:
        >>> (
        ...     start(3)
        ...     >> tap[int, Any](lambda x: double(x))  # typed lambda
        ...     >> tap(lambda _: print("ok"))  # lambda
        ...     >> pipe(double)
        ...     >> tap(double)  # function
        ...     >> tap(async_add, 3)  # async function with args
        ...     >> pipe(BasicClass)
        ...     >> tap(BasicClass.increment)  # Updates original object
        ...     >> tap(BasicClass.my_method, 5)  # method with arg
        ...     >> tap(BasicClass.my_classmethod)  # classmethod
        ...     >> then[BasicClass, str](lambda x: x.value)
        ...     >> end()
        ... )
        7  # Because `BasicClass.increment` updated the original object
    """

    __slots__ = ("f", "args", "kwargs")

    f: PipeableCallable[TInput, FuncParams, Any]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __init__(
        self,
        f: PipeableCallable[TInput, FuncParams, Any],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]:
        """Runs the function and returns the unchanged PipeObject."""
        f = self.f
        if is_sync_pipeable(f):
            f(other.value, *self.args, **self.kwargs)
        else:
            asyncio.run(f(other.value, *self.args, **self.kwargs))
        return other.retain()


# region TaskPipe
class TaskPipe(Generic[TInput, FuncParams]):
    """
    Non-blocking pipeable that runs the function in a new thread and returns the unchanged PipeObject.
    Perfect for background tasks and parallelization.
    Tasks can then be waited for with the `wait` pipeable.

    Args:
        task_id (TaskId): ID of the task (unique within the current pipe).
        f (PipeableCallable[TInput, FuncParams, Any]): Function to run in a new thread.
        args (FuncParams.args): The args (except the first) to pass to the function.
        kwargs (FuncParams.kwargs): The kwargs to pass to the function.

    Example:
        >>> (
        ...     start("3")
        ...     >> task[str, Any]("t1", lambda x: do_something(x))  # typed lambda
        ...     >> task("t2", lambda _: print("ok"))  # lambda
        ...     >> pipe(int)
        ...     >> task("t3", do_something_else)  # function
        ...     >> task("t4", async_do_something)  # async function
        ...     >> pipe(BasicClass)
        ...     >> task("t5", BasicClass.increment)  # method (updates original object)
        ...     >> task("t7", BasicClass.my_method, 5)  # method with arg
        ...     >> task("t6", BasicClass.my_classmethod)  # classmethod
        ...     >> then[BasicClass, str](lambda x: x.value)
        ...     >> wait()
        ...     >> end()
        ... )
        4  # Because `BasicClass.increment` updated the original object
    """

    __slots__ = ("f", "args", "kwargs", "task_id")

    f: PipeableCallable[TInput, FuncParams, Any]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    task_id: TaskId

    def __init__(
        self,
        task_id: TaskId,
        f: PipeableCallable[TInput, FuncParams, Any],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.task_id = task_id
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]:
        """Runs the function in a new thread and returns the PipeObject unchanged."""
        f = self.f
        value = other.value
        args = self.args
        kwargs = self.kwargs
        if is_async_pipeable(f):
            thread = Thread(target=lambda: asyncio.run(f(value, *args, **kwargs)))
        else:
            thread = Thread(target=f, args=(value, *args), kwargs=kwargs)
        other.register_thread(self.task_id, thread)
        return other.retain()


# region WaitFor
class WaitFor:
    """
    Pipeable that waits for some or all tasks to complete before returning the unchanged PipeObject.
    Works in pair with `task`.

    Args:
        task_ids (Optional[List[TaskId]]): List of task IDs to wait for.

    Example:
        >>> (
        ...     start(3)
        ...     >> pipe(str)
        ...     >> task("t1", do_something)
        ...     >> wait(["t1"])  # wait for task "t1" to complete
        ...     >> task("t2", do_something_else, arg1, arg2)
        ...     >> wait()  # wait for all remaining tasks
        ...     >> end()
        ... )
        "3"
    """

    __slots__ = ("task_ids",)

    task_ids: Optional[List[TaskId]]

    def __init__(self, task_ids: Optional[List[TaskId]] = None) -> None:
        self.task_ids = task_ids

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]:
        """Waits for tasks to complete before returning the unchanged PipeObject."""
        other.wait_for_tasks(self.task_ids)
        return other.retain()


# region PipeEnd
class PipeEnd:
    """
    End of the pipe chain which returns the raw value of the final PipeObject.
    Cannot continue the pipe chain after this.

    Example:
        >>> start(3) >> pipe(str) >> end()
        "3"
    """

    __slots__ = ()

    def __rrshift__(self, other: PipeObject[TValue]) -> TValue:
        """Returns the raw value of the PipeObject."""
        return cast(TValue, other.value)
