import asyncio
import time
from unittest import TestCase

from pipe_operator.python_flow.base import (
    PipeEnd,
    PipeStart,
)
from pipe_operator.python_flow.threads import ThreadPipe, ThreadWait
from pipe_operator.shared.exceptions import PipeError


async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


class ThreadTestCase(TestCase):
    def test_with_threads_without_join(self) -> None:
        start = time.perf_counter()
        op = (
            PipeStart(3)
            >> ThreadPipe("t1", lambda _: time.sleep(0.2))
            >> ThreadPipe("t2", lambda _: time.sleep(0.2))
            >> PipeEnd()
        )
        delta = time.perf_counter() - start
        # We did not wait for the threads to finish
        self.assertTrue(delta < 0.1)
        self.assertEqual(op, 3)

    def test_with_threads_with_some_joins(self) -> None:
        start = time.perf_counter()
        op = (
            PipeStart(3)
            >> ThreadPipe("t1", lambda _: time.sleep(0.1))
            >> ThreadPipe("t2", lambda _: time.sleep(0.2))
            >> ThreadWait(["t1"])
            >> PipeEnd()
        )
        delta = time.perf_counter() - start
        # We waited for the 1s thread only
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 3)

    def test_with_threads_with_join_all(self) -> None:
        start = time.perf_counter()
        op = (
            PipeStart(3)
            >> ThreadPipe("t1", lambda _: time.sleep(0.1))
            >> ThreadPipe("t2", lambda _: time.sleep(0.2))
            >> ThreadWait()
            >> PipeEnd()
        )
        delta = time.perf_counter() - start
        # We waited for all threads
        self.assertTrue(delta > 0.2)
        self.assertTrue(delta < 0.3)
        self.assertEqual(op, 3)

    def test_with_threads_with_unknown_thread_id(self) -> None:
        with self.assertRaises(PipeError):
            _ = (
                PipeStart(3)
                >> ThreadPipe("t1", lambda _: time.sleep(0.2))
                >> ThreadWait(["t2"])
                >> PipeEnd()
            )

    def test_with_threads_with_duplicated_thread_id(self) -> None:
        with self.assertRaises(PipeError):
            _ = (
                PipeStart(3)
                >> ThreadPipe("t1", lambda _: time.sleep(0.2))
                >> ThreadPipe("t1", lambda _: time.sleep(0.2))
                >> PipeEnd()
            )

    def test_does_not_support_async_functions(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> ThreadPipe("t1", async_add_one) >> PipeEnd()
