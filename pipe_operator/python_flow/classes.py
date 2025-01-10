from abc import ABC, abstractmethod
import asyncio
from threading import Thread
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Union,
    cast,
    overload,
)

from typing_extensions import Self, override

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
    __slots__ = ("value", "debug", "history", "tasks")

    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.history: List[Any] = []
        self.tasks: Dict[TaskId, Thread] = {}
        self._handle_debug()

    def update(self, value: TNewValue) -> "PipeObject[TNewValue]":
        self.value = value  # type: ignore
        self._handle_debug()
        return cast("PipeObject[TNewValue]", self)

    def retain(self) -> Self:
        self._handle_debug()
        return self

    def register_thread(self, task_id: TaskId, thread: Thread) -> None:
        if task_id in self.tasks:
            raise PipeError(f"Task ID {task_id} already exists")
        self.tasks[task_id] = thread
        thread.start()

    def wait_for_tasks(self, task_ids: Optional[List[TaskId]] = None) -> None:
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
        cast_value = cast(TInput, other.value)
        result = self.f(cast_value, *self.args, **self.kwargs)
        return other.update(result)


# region AsyncPipe
class AsyncPipe(Generic[TInput, FuncParams, TOutput]):
    __slots__ = ("f", "args", "kwargs")

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
        value = asyncio.run(self.f(other.value, *self.args, **self.kwargs))  # type: ignore
        return other.update(value)


# region PipeFactory
class PipeFactory(Generic[TInput, FuncParams, TOutput]):
    @overload
    def __new__(  # type: ignore
        cls,
        f: AsyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> AsyncPipe[TInput, FuncParams, TOutput]: ...

    @overload
    def __new__(  # type: ignore
        cls,
        f: SyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> Pipe[TInput, FuncParams, TOutput]: ...

    def __new__(  # type: ignore
        cls,
        f: PipeableCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> Union[
        Pipe[TInput, FuncParams, TOutput], AsyncPipe[TInput, FuncParams, TOutput]
    ]:
        if is_lambda(f):
            raise PipeError(
                "`pipe` does not support lambda functions. Use `then` instead."
            )
        if is_sync_pipeable(f):
            return Pipe(f, *args, **kwargs)
        if is_async_pipeable(f):
            return AsyncPipe(f, *args, **kwargs)
        raise PipeError("Unsupported function provided to `pipe`.")

    def __rrshift__(self, _other: PipeObject[TInput]) -> PipeObject[TOutput]:
        if isinstance(self, AsyncPipe) or isinstance(self, Pipe):
            return self.__rrshift__(_other)
        raise PipeError("Unsupported function provided to `pipe`.")


# region Then
class Then(Generic[TInput, TOutput]):
    __slots__ = ("f",)

    def __init__(self, f: Callable[[TInput], TOutput]) -> None:
        if not is_one_arg_lambda(f):
            raise PipeError("`then` only supports one-arg lambdas. Try `pipe` instead.")
        self.f = f

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TOutput]:
        value = self.f(other.value)
        return other.update(value)


# region _SideEffect
class _SideEffect(ABC, Generic[TInput, FuncParams]):
    __slots__ = ("f", "args", "kwargs")

    def __init__(
        self,
        f: PipeableCallable[TInput, FuncParams, Any],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]: ...


# region Tap
class Tap(_SideEffect[TInput, FuncParams]):
    @override
    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]:
        if is_async_pipeable(self.f):
            asyncio.run(self.f(other.value, *self.args, **self.kwargs))  # type: ignore
        else:
            cast_value = cast(TInput, other.value)
            self.f(cast_value, *self.args, **self.kwargs)
        return other.retain()


# region TaskPipe
class TaskPipe(_SideEffect[TInput, FuncParams]):
    __slots__ = _SideEffect.__slots__ + ("task_id",)

    @override
    def __init__(
        self,
        task_id: TaskId,
        f: PipeableCallable[TInput, FuncParams, Any],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.task_id = task_id
        super().__init__(f, *args, **kwargs)

    @override
    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]:
        if is_async_pipeable(self.f):
            thread = Thread(
                target=lambda: asyncio.run(
                    self.f(other.value, *self.args, **self.kwargs)  # type: ignore
                )
            )
        else:
            args = (other.value, *self.args)
            kwargs: Any = self.kwargs or {}
            thread = Thread(target=self.f, args=args, kwargs=kwargs)
        other.register_thread(self.task_id, thread)
        return other.retain()


# region WaitFor
class WaitFor:
    __slots__ = ("task_ids",)

    def __init__(self, task_ids: Optional[List[TaskId]] = None) -> None:
        self.task_ids = task_ids

    def __rrshift__(self, other: PipeObject[TInput]) -> PipeObject[TInput]:
        other.wait_for_tasks(self.task_ids)
        return other.retain()


# region PipeEnd
class PipeEnd:
    __slots__ = ()

    def __rrshift__(self, other: PipeObject[TValue]) -> TValue:
        return cast(TValue, other.value)
