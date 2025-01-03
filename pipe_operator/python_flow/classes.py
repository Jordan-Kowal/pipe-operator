from abc import ABC, abstractmethod
import asyncio
from threading import Thread
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Self,
    TypeAlias,
    Union,
    override,
)

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
from pipe_operator.python_flow.utils import is_async_pipeable
from pipe_operator.shared.exceptions import PipeError
from pipe_operator.shared.utils import is_one_arg_lambda


# region PipeObject
class PipeObject(Generic[TValue]):
    __slots__ = ("value", "debug", "result", "history", "tasks")

    def __init__(self, value: TValue, debug: bool = False) -> None:
        self.value = value
        self.debug = debug
        self.history: List[Any] = []
        self.result: Optional[Any] = None
        self.tasks: Dict[TaskId, Thread] = {}
        self._handle_debug()

    @classmethod
    def update(
        cls, pipe_start: "PipeObject[TValue]", value: TNewValue
    ) -> "PipeObject[TNewValue]":
        pipe_start.value = value  # type: ignore
        pipe_start._handle_debug()
        return pipe_start  # type: ignore

    def keep(self) -> Self:
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


Other: TypeAlias = Union[PipeObject[TInput], PipeObject[Coroutine[Any, Any, TInput]]]


# region _Pipeable
class _Pipeable(ABC, Generic[TInput, FuncParams, TOutput]):
    __slots__ = ("f", "args", "kwargs")

    def __init__(
        self,
        f: PipeableCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        self.f = f
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TOutput]: ...


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
    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TInput]: ...


# region Pipe
class Pipe(_Pipeable[TInput, FuncParams, TOutput]):
    @override
    def __init__(
        self,
        f: SyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        super().__init__(f, *args, **kwargs)

    @override
    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TOutput]:
        value = self.f(other.value, *self.args, **self.kwargs)  # type: ignore
        return PipeObject.update(other, value)  # type: ignore


# region AsyncPipe
class AsyncPipe(_Pipeable[TInput, FuncParams, TOutput]):
    @override
    def __init__(
        self,
        f: AsyncCallable[TInput, FuncParams, TOutput],
        *args: FuncParams.args,
        **kwargs: FuncParams.kwargs,
    ) -> None:
        super().__init__(f, *args, **kwargs)

    @override
    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TOutput]:
        value = asyncio.run(self.f(other.value, *self.args, **self.kwargs))  # type: ignore
        return PipeObject.update(other, value)  # type: ignore


# region Then
class Then(Generic[TInput, TOutput]):
    __slots__ = ("f",)

    def __init__(self, f: Callable[[TInput], TOutput]) -> None:
        if not is_one_arg_lambda(f):
            raise PipeError("`then` only supports one-arg lambdas. Try `pipe` instead.")
        self.f = f

    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TOutput]:
        value = self.f(other.value)
        return PipeObject.update(other, value)  # type: ignore


# region Tap
class Tap(_SideEffect[TInput, FuncParams]):
    @override
    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TInput]:
        if is_async_pipeable(self.f):
            asyncio.run(self.f(other.value, *self.args, **self.kwargs))  # type: ignore
        else:
            self.f(other.value, *self.args, **self.kwargs)  # type: ignore
        return other.keep()  # type: ignore


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
    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TInput]:
        args = (other.value, *self.args)
        if is_async_pipeable(self.f):
            thread = Thread(target=lambda: asyncio.run(self.f(*args, **self.kwargs)))  # type: ignore
        else:
            thread = Thread(target=self.f, args=args, kwargs=self.kwargs)  # type: ignore
        other.register_thread(self.task_id, thread)
        return other.keep()  # type: ignore


# region WaitFor
class WaitFor:
    __slots__ = ("task_ids",)

    def __init__(self, task_ids: Optional[List[TaskId]] = None) -> None:
        self.task_ids = task_ids

    def __rrshift__(self, other: Other[TInput]) -> PipeObject[TInput]:
        other.wait_for_tasks(self.task_ids)
        return other.keep()  # type: ignore


# region PipeEnd
class PipeEnd:
    __slots__ = ()

    def __rrshift__(self, other: Other[TValue]) -> TValue:
        return other.value  # type: ignore
