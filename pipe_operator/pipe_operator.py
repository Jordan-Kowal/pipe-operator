import ast
from inspect import getsource, isclass, stack
from textwrap import dedent
from typing import Callable, Optional

from pipe_operator.transformers import PipeTransformer


def pipes(func: Optional[Callable] = None) -> Callable:
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
        tree = PipeTransformer().visit(tree)
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
