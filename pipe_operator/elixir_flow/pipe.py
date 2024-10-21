import ast
from inspect import getsource, isclass, stack
from itertools import takewhile
from textwrap import dedent
from typing import Any, Callable, Optional, TypeVar

from pipe_operator.elixir_flow.transformers import (
    DEFAULT_LAMBDA_VAR,
    DEFAULT_OPERATOR,
    DEFAULT_PLACEHOLDER,
    PipeTransformer,
)
from pipe_operator.elixir_flow.utils import OperatorString
from pipe_operator.shared.utils import is_one_arg_lambda


def elixir_pipe(
    func: Optional[Callable] = None,
    operator: OperatorString = DEFAULT_OPERATOR,
    placeholder: str = DEFAULT_PLACEHOLDER,
    lambda_var: str = DEFAULT_LAMBDA_VAR,
    debug: bool = False,
) -> Callable:
    """
    Allows the decorated function to use an elixir pipe-like syntax.
    The decorator can be called with or without parenthesis.
    The following instructions are supported:
        class calls                         a >> B(...)                         B(a, ...)
        method calls                        a >> _.method(...)                  a.method(...)
        property calls                      a >> _.property                     a.property
        binary operators                    a >> _ + 3                          (lambda Z: Z + 3)(a)
        f-strings                           a >> f"{_}"                         (lambda Z: f"{Z}")(a)
        list/set/... creations              a >> [_, 1, 2]                      (lambda Z: [Z, 1, 2])(a)
        list/set/... comprehensions         a >> [x + _ for x in range(_)]      (lambda Z: [x + Z for x in range(Z)])(a)
        function calls                      a >> b(...)                         b(a, ...)
        calls without parenthesis           a >> b                              b(a)
        lambda calls                        a >> (lambda x: x + 4)              (lambda x: x + 4)(a)

    Args:
        func (Optional[Callable], optional): The function to decorate.
            Defaults to None.
        operator (OperatorString, optional): The operator to use as the pipe.
            Defaults to DEFAULT_OPERATOR.
        placeholder (str, optional): The placeholder variable used in method, attribute, and binary calls.
            Defaults to DEFAULT_PLACEHOLDER.
        lambda_var (str, optional): The variable used in generated lambda functions.
            Defaults to DEFAULT_LAMBDA_VAR.
        debug (bool, optional): Whether to print the output after each pipe operation.
            Defaults to False.

    Returns:
        Callable: The decorated function.

    Examples:
        >>> # Defines a bunch of functions/classes for our example:
        >>> def add(a: int, b: int) -> int:
        ...     return a + b
        >>> def double(a: int) -> int:
        ...     return 2 * a
        >>> def _sum(*args: int) -> int:
        ...     return sum(args)
        >>> class BasicClass:
        ...     def __init__(self, value: int) -> None:
        ...         self.value = value
        ...
        ...     @property
        ...     def get_value_property(self) -> int:
        ...         return self.value
        ...
        ...     def get_value_method(self) -> int:
        ...         return self.value
        ...
        ...     def get_value_plus_arg(self, value: int) -> int:
        ...         return self.value + value
        >>> # Defines a decorated function that uses the pipe-like syntax.
        >>> # This is a complex case, but it shows how to use the decorator:
        >>> @elixir_pipe
        ... def run() -> None:
        ...     return (
        ...         1
        ...         >> BasicClass
        ...         >> _.value
        ...         >> BasicClass()
        ...         >> _.get_value_property
        ...         >> BasicClass()
        ...         >> _.get_value_method()
        ...         >> BasicClass()
        ...         >> _.get_value_plus_arg(10)
        ...         >> 10 + _ - 5
        ...         >> {_, 1, 2, 3}
        ...         >> [x for x in _ if x > 4]
        ...         >> (lambda x: x[0])
        ...         >> double
        ...         >> tap(double)
        ...         >> double()
        ...         >> add(1)
        ...         >> _sum(2, 3)
        ...         >> (lambda a: a * 2)
        ...         >> then(lambda a: a + 1)
        ...         >> f"value is {_}"
        ...     )
        >>> # Call the decorated function:
        >>> run()
        "value is 140"
    """

    def wrapper(func_or_class: Callable) -> Callable:
        if isclass(func_or_class):
            # [2] because we are at elixir_pipe() > wrapper()
            decorator_frame = stack()[2]
            ctx = decorator_frame[0].f_locals
            first_line_number = decorator_frame[2]
        else:
            ctx = func_or_class.__globals__
            first_line_number = func_or_class.__code__.co_firstlineno

        # Extract AST
        source = getsource(func_or_class)
        tree = ast.parse(dedent(source))

        # Increment line/column numbers
        ast.increment_lineno(tree, first_line_number - 1)
        source_indent = sum([1 for _ in takewhile(str.isspace, source)]) + 1
        for node in ast.walk(tree):
            if hasattr(node, "col_offset"):
                node.col_offset += source_indent  # noqa # type: ignore
                node.end_col_offset += source_indent  # type: ignore

        # Remove the @elixir_pipe decorator and @elixir_pipe() decorators from the AST to avoid recursive calls
        tree.body[0].decorator_list = [  # type: ignore
            d
            for d in tree.body[0].decorator_list  # type: ignore
            if isinstance(d, ast.Call)
            and d.func.id != "elixir_pipe"  # type: ignore
            or isinstance(d, ast.Name)
            and d.id != "elixir_pipe"
        ]

        # Update the AST and execute the new code
        transformer = PipeTransformer(
            operator=operator,
            placeholder=placeholder,
            lambda_var=lambda_var,
            debug_mode=debug,
        )
        tree = transformer.visit(tree)
        code = compile(
            tree,
            filename=(ctx["__file__"] if "__file__" in ctx else "repl"),
            mode="exec",
        )
        exec(code, ctx)
        return ctx[tree.body[0].name]

    # If decorator called without parenthesis `@elixir_pipe`
    if func and callable(func):
        return wrapper(func)

    return wrapper


T = TypeVar("T")
R = TypeVar("R")


def tap(value: T, func_or_class: Callable[[T], Any]) -> T:
    """
    Given a function, calls it with the value and returns the value.

    Args:
        value (T): The value to pass to the function and to return.
        func_or_class (Callable[[T], Any]): The function/class to call.

    Returns:
        T: The original value.

    Examples:
        >>> tap(42, print)
        42
        42

        >>> tap(42, lambda x: print(x + 1))
        43
        42
    """
    func_or_class(value)
    return value


def then(value: T, f: Callable[[T], R]) -> R:
    """
    Elixir-like `then` function to pass a lambda into the pipe.
    Simply calls f(value).

    Args:
        value (T): The value to pass to the function
        f (Callable[[T], R]): The function/class to call.

    Returns:
        R: The result of the function call.

    Raises:
        TypeError: If the function is not a lambda function.

    Examples:
        >>> then(42, lambda x: x + 1)
        43
    """
    if not is_one_arg_lambda(f):
        raise TypeError(
            "[pipe_operator] `Then` only supports lambda functions. Use `Pipe` instead."
        )
    return f(value)
