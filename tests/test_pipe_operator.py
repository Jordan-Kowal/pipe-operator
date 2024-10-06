import unittest

from pipe_operator import pipes


def add2(a, b):
    return a + b


def add3(a, b, c):
    return a + b + c


class PipeOpTestCase(unittest.TestCase):
    @pipes
    def test_pipe_one_arg(self):
        assert [1, 2, 3] >> sum() == 6

    @pipes
    def test_pipe_two_args(self):
        assert 1 >> add2(2) == 3

    @pipes
    def test_pipe_three_args(self):
        assert 1 >> add3(2, 3) == 6

    @pipes
    def test_left_pipe(self):
        assert 2 << pow(3) == 9

    @pipes
    def test_pipe_one_arg_no_braces(self):
        assert [1, 2, 3] >> sum == 6

    @pipes
    def test_left_pipe_one_arg_no_braces(self):
        assert [1, 2, 3] << sum == 6

    @pipes
    def test_multiline(self):
        assert (
            range(-5, 0) << map(lambda x: x + 1) << map(abs) << map(str) >> tuple
        ) == ("4", "3", "2", "1", "0")

    @pipes
    def test_lambda_no_braces(self):
        assert 5 << (lambda a: a**2) == 25

    def test_method_no_braces(self):
        cup = ClassUsingPipes()
        assert cup.foo() == 256

    def test_class_decorator(self):
        cup = ClassUsingPipes2()
        assert cup.foo() == 256

    @pipes
    def test_chaining(self):
        assert range(-5, 0) << map(abs) >> list == [5, 4, 3, 2, 1]


class ClassUsingPipes:
    def __init__(self):
        pass

    def squared(self, a):
        return a**a

    @pipes
    def foo(self):
        return range(-2, 2) << map(abs) << sum << self.squared


@pipes
class ClassUsingPipes2(object):
    zero = 0

    def __init__(self):
        pass

    def squared(self, a):
        return a >> pow(a)

    def foo(self):
        return range(-2, 2) << map(abs) << sum << self.squared >> add2(self.zero)
