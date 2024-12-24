import asyncio
import time
from unittest import TestCase

from pipe_operator.python_flow.asynchronous import AsyncPipe
from pipe_operator.python_flow.base import (
    PipeEnd,
    PipeStart,
)
from pipe_operator.shared.exceptions import PipeError


async def async_add_one(value: int) -> int:
    await asyncio.sleep(0.1)
    return value + 1


def add_one(value: int) -> int:
    return value + 1


class AsyncTestCase(TestCase):
    def test_async_pipe(self) -> None:
        start = time.perf_counter()
        op = PipeStart(3) >> AsyncPipe(async_add_one) >> PipeEnd()
        delta = time.perf_counter() - start
        # We waited for the 1s from async_add_one
        self.assertTrue(delta > 0.1)
        self.assertTrue(delta < 0.2)
        self.assertEqual(op, 4)

    def test_does_not_support_regular_functions(self) -> None:
        with self.assertRaises(PipeError):
            _ = PipeStart(3) >> AsyncPipe(add_one) >> PipeEnd()  # type: ignore
