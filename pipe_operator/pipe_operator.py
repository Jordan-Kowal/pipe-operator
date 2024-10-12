import ast
from inspect import getsource, isclass, stack
from textwrap import dedent
from typing import Any, Callable, Optional, TypeVar

from pipe_operator.transformers import (
    DEFAULT_LAMBDA_VAR,
    DEFAULT_OPERATOR,
    DEFAULT_PLACEHOLDER,
    PipeTransformer,
)
from pipe_operator.utils import OperatorString


def pipes(
    func: Optional[Callable] = None,
    operator: OperatorString = DEFAULT_OPERATOR,
    placeholder: str = DEFAULT_PLACEHOLDER,
    lambda_var: str = DEFAULT_LAMBDA_VAR,
) -> Callable:
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
        tree.body[0].decorator_list = [
            d
            for d in tree.body[0].decorator_list
            if isinstance(d, ast.Call)
            and d.func.id != "pipes"
            or isinstance(d, ast.Name)
            and d.id != "pipes"
        ]

        # Update the AST and execute the new code
        transformer = PipeTransformer(
            operator=operator, placeholder=placeholder, lambda_var=lambda_var
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
    """Calls a function with the value but returns the original value"""
    func_or_class(value)
    return value
