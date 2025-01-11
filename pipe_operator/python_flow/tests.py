import asyncio
import time
from typing import Any
from unittest import TestCase
from unittest.mock import Mock, patch

from pipe_operator.python_flow.classes import PipeEnd as end
from pipe_operator.python_flow.classes import PipeFactory as pipe
from pipe_operator.python_flow.classes import PipeObject as start
from pipe_operator.python_flow.classes import Tap as tap
from pipe_operator.python_flow.classes import TaskPipe as task
from pipe_operator.python_flow.classes import Then as then
from pipe_operator.python_flow.classes import WaitFor as wait
from pipe_operator.shared.exceptions import PipeError


# region Setup
async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


def int_to_string(x: int) -> str:
    return str(x)


def string_to_int(x: str) -> int:
    return int(x)


def double(x: int) -> int:
    return x * 2


def duplicate_string(x: str) -> str:
    return f"{x}{x}"


def compute(x: int, y: int, z: int = 0) -> int:
    return x + y + z


def _sum(*args: int) -> int:
    return sum(args)


class BasicClass:
    def __init__(self, value: int) -> None:
        self.value = value

    def increment(self) -> None:
        self.value += 1

    @property
    def get_value_property(self) -> int:
        return self.value

    def get_value_method(self) -> int:
        return self.value

    def get_value_plus_arg(self, value: int) -> int:
        return self.value + value

    @classmethod
    def get_double(cls, instance: "BasicClass") -> "BasicClass":
        return BasicClass(instance.value * 2)


class CompleteFlowTestCase(TestCase):
    def test_complex(self) -> None:
        with patch("builtins.print"):
            op = (
                start("3", debug=True)
                >> pipe(duplicate_string)  # function
                >> then[str, int](lambda x: int(x))  # lambda
                >> pipe(async_add_one)  # async function
                >> task("t1", lambda _: time.sleep(0.2))  # (side effect) lambda task
                >> pipe(compute, 30, z=10)  # function with args/kwargs
                >> task("t2", async_add_one)  # (side effect) async task
                >> pipe(_sum, 5, 10)  # function with no positional args  # type: ignore
                >> wait(["t1"])  # wait for a specific task
                >> pipe(BasicClass)  # class
                >> pipe(BasicClass.get_double)  # classmethod
                >> tap(BasicClass.increment)  # (side effect) method
                >> pipe(BasicClass.get_value_plus_arg, 5)  # method with arg
                >> tap(lambda x: print(x))  # (side effect) lambda
                >> wait()  # wait for all remaining tasks
                >> end()
            )
        self.assertEqual(op, 184)

    def test_complex_with_debug(self) -> None:
        _start = time.perf_counter()
        with patch("builtins.print"):
            instance = (
                start("3", debug=True)
                >> pipe(duplicate_string)  # function
                >> then[str, int](lambda x: int(x))  # lambda
                >> pipe(async_add_one)  # async function
                >> task("t1", lambda _: time.sleep(0.2))  # (side effect) lambda task
                >> pipe(compute, 30, z=10)  # function with args/kwargs
                >> task("t2", async_add_one)  # (side effect) async task
                >> pipe(_sum, 5, 10)  # function with no positional args  # type: ignore
                >> wait(["t1"])  # wait for a specific task
                >> pipe(BasicClass)  # class
                >> pipe(BasicClass.get_double)  # classmethod
                >> tap(BasicClass.increment)  # (side effect) method
                >> pipe(BasicClass.get_value_plus_arg, 5)  # method with arg
                >> tap(lambda x: print(x))  # (side effect) lambda
                >> wait()  # wait for all remaining tasks
            )
        op: int = instance >> end()
        normalized_history = [
            x.value if isinstance(x, BasicClass) else x for x in instance.history
        ]
        self.assertListEqual(
            normalized_history,
            ["3", "33", 33, 34, 34, 74, 74, 89, 89, 89, 179, 179, 184, 184, 184],
        )
        delta = time.perf_counter() - _start
        self.assertTrue(delta > 0.3)
        self.assertTrue(delta < 0.4)
        self.assertEqual(op, 184)


# region PipeTestCase
class PipeTestCase(TestCase):
    def test_supported_pipeables(self) -> None:
        _start = time.perf_counter()
        op = (
            start("3")
            >> pipe(string_to_int)  # function
            >> pipe(async_add_one)  # async function
            >> pipe(compute, 30, z=10)  # function with args/kwargs
            >> pipe(_sum, 5, 10)  # function with no positional args  # type: ignore
            >> pipe(BasicClass)  # class
            >> pipe(BasicClass.get_double)  # classmethod
            >> pipe(BasicClass.get_value_plus_arg, 5)  # method with arg
            >> end()
        )
        delta = time.perf_counter() - _start
        # We waited for the 1s from async_add_one
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 123)

    def test_fails_with_lambdas(self) -> None:
        with self.assertRaises(PipeError):
            pipe(lambda x: x + 1)  # noqa: # type: ignore


# region ThenTestCase
class ThenTestCase(TestCase):
    def test_with_one_arg_lambdas(self) -> None:
        op = (
            start(3)
            >> then[int, int](lambda x: x + 1)
            >> then[int, str](lambda x: str(x))
            >> end()
        )
        self.assertEqual(op, "4")

    def test_if_function_is_not_1_arg_lambda(self) -> None:
        with self.assertRaises(PipeError):
            then(lambda x, y: x + y)  # type: ignore
        with self.assertRaises(PipeError):
            then(string_to_int)
        with self.assertRaises(PipeError):
            then(async_add_one)
        with self.assertRaises(PipeError):
            then(compute)  # type: ignore
        with self.assertRaises(PipeError):
            then(_sum)
        with self.assertRaises(PipeError):
            then(BasicClass)
        with self.assertRaises(PipeError):
            then(BasicClass.get_double)
        with self.assertRaises(PipeError):
            then(BasicClass.get_value_plus_arg)  # type: ignore


# region TapTestCase
class TapTestCase(TestCase):
    def test_supported_pipeables(self) -> None:
        mock = Mock()
        op = (
            start(3)
            >> tap[int, Any](lambda x: double(x))  # typed lambda
            >> tap(lambda _: mock(12))  # lambda
            >> pipe(double)
            >> tap(int_to_string)  # function
            >> tap(async_add_one)  # async function
            >> pipe(BasicClass)
            >> tap(BasicClass.increment)  # Updates original object
            >> tap(BasicClass.get_double)  # classmethod
            >> tap(BasicClass.get_value_plus_arg, 5)  # method with arg
            >> pipe(BasicClass.get_value_method)
            >> end()
        )
        self.assertEqual(op, 7)
        mock.assert_called_once_with(12)


# region TaskTestCase
class TaskTestCase(TestCase):
    def test_supported_pipeables(self) -> None:
        mock = Mock()
        op = (
            start(3)
            >> task[int, Any]("t1", lambda x: double(x))  # typed lambda
            >> task("t2", lambda _: mock(12))  # lambda
            >> pipe(double)
            >> task("t3", int_to_string)  # function
            >> task("t4", async_add_one)  # async function
            >> pipe(BasicClass)
            >> task("t5", BasicClass.increment)  # Updates original object
            >> task("t6", BasicClass.get_double)  # classmethod
            >> task("t7", BasicClass.get_value_plus_arg, 5)  # method with arg
            >> pipe(BasicClass.get_value_method)
            >> wait()
            >> end()
        )
        self.assertEqual(op, 7)
        mock.assert_called_once_with(12)

    def test_without_join(self) -> None:
        _start = time.perf_counter()
        op = (
            start(3)
            >> task("t1", lambda _: time.sleep(0.2))  # function
            >> task("t2", async_add_one)  # async function
            >> end()
        )
        delta = time.perf_counter() - _start
        # We did not wait for the threads to finish
        self.assertTrue(delta < 0.1)
        self.assertEqual(op, 3)

    def test_with_some_joins(self) -> None:
        _start = time.perf_counter()
        op: int = (
            start(3)
            >> task("t1", lambda _: time.sleep(0.2))  # function
            >> task("t2", async_add_one)  # async function
            >> wait(["t2"])
            >> end()
        )
        delta = time.perf_counter() - _start
        # We waited for the 1s thread only
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 3)

    def test_with_join_all(self) -> None:
        _start = time.perf_counter()
        op: int = (
            start(3)
            >> task("t1", lambda _: time.sleep(0.05))  # function
            >> task("t2", async_add_one)  # async function
            >> wait()
            >> end()
        )
        delta = time.perf_counter() - _start
        # We waited for all threads
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 3)

    def test_should_crash_on_unknown_task_id(self) -> None:
        with self.assertRaises(PipeError):
            _ = (
                start(3)
                >> task("t1", lambda _: time.sleep(0.2))
                >> wait(["t2"])
                >> end()
            )

    def test_should_crash_on_duplicate_task_id(self) -> None:
        with self.assertRaises(PipeError):
            _ = (
                start(3)
                >> task("t1", lambda _: time.sleep(0.2))
                >> task("t1", lambda _: time.sleep(0.2))
                >> end()
            )
