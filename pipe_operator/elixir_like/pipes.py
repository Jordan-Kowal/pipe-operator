import ast
from inspect import getsource, isclass, stack
import pdb
from textwrap import dedent
from typing import Any, Callable, Optional, TypeVar

from pipe_operator.elixir_like.transformers import (
    DEFAULT_LAMBDA_VAR,
    DEFAULT_OPERATOR,
    DEFAULT_PLACEHOLDER,
    PipeTransformer,
)
from pipe_operator.elixir_like.utils import OperatorString


def pipes(
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
        Define functions and classes for our pipes to use:

        >>> def add(a: int, b: int) -> int:
        >>>     return a + b

        >>> def double(a: int) -> int:
        >>>     return 2 * a

        >>> def _sum(*args: int) -> int:
        >>>     return sum(args)

        >>> class BasicClass:
        >>>     def __init__(self, value: int) -> None:
        >>>         self.value = value

        >>>     @property
        >>>     def get_value_property(self) -> int:
        >>>         return self.value

        >>>     def get_value_method(self) -> int:
        >>>         return self.value

        >>>     def get_value_plus_arg(self, value: int) -> int:
        >>>         return self.value + value

        Defines a decorated function that uses the pipe-like syntax.
        This is a complex case, but it shows how to use the decorator:

        >>> @pipes
        >>> def run() -> None:
        >>>     return (
        >>>         1
        >>>         >> BasicClass
        >>>         >> _.value
        >>>         >> BasicClass()
        >>>         >> _.get_value_property
        >>>         >> BasicClass()
        >>>         >> _.get_value_method()
        >>>         >> BasicClass()
        >>>         >> _.get_value_plus_arg(10)
        >>>         >> 10 + _ - 5
        >>>         >> {_, 1, 2, 3}
        >>>         >> [x for x in _ if x > 4]
        >>>         >> (lambda x: x[0])
        >>>         >> double
        >>>         >> tap(double)
        >>>         >> double()
        >>>         >> add(1)
        >>>         >> _sum(2, 3)
        >>>         >> (lambda a: a * 2)
        >>>         >> f"value is {_}"
        >>>     )

        Call the decorated function:

        >>> run()
        value is 140
    """

    def wrapper(func_or_class: Callable) -> Callable:
        if isclass(func_or_class):
            # [2] because we are at pipes() > wrapper()
            ctx = stack()[2][0].f_locals
        else:
            ctx = func_or_class.__globals__

        # Extract AST
        source = getsource(func_or_class)
        tree = ast.parse(dedent(source))

        # Remove the @pipes decorator and @pipes() decorators from the AST to avoid recursive calls
        tree.body[0].decorator_list = [  # type: ignore
            d
            for d in tree.body[0].decorator_list  # type: ignore
            if isinstance(d, ast.Call)
            and d.func.id != "pipes"  # type: ignore
            or isinstance(d, ast.Name)
            and d.id != "pipes"
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

    # If decorator called without parenthesis `@pipes`
    if func and callable(func):
        return wrapper(func)

    return wrapper


T = TypeVar("T")


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


def start_pdb(x: T = None) -> T:
    """
    Shortcut to start the pdb debugger in the pipe.
    Using `tap`, it starts the pdb debugger and returns the original value.

    Args:
        x (T, optional): The value to return. Defaults to None.

    Returns:
        T: The original value.

    Examples:
        >>> result = start_pdb(100)
        # This will trigger the pdb debugger, allowing you to step through the code.
        # After exiting the debugger, the value `100` will be returned.
        >>> print(result)
        100
    """
    return tap(x, lambda _: pdb.set_trace())
