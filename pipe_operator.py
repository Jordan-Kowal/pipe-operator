import ast
from ast import (
    Call,
    LShift,
    Name,
    NodeTransformer,
    RShift,
    parse,
)
from inspect import getsource, isclass, stack
from textwrap import dedent
from typing import Callable


class PipeTransformer(NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if not isinstance(node.op, (LShift, RShift)):
            return node
        # Convert function name / lambda etc without braces into call
        if not isinstance(node.right, Call):
            call = Call(
                func=node.right,
                args=[node.left],
                keywords=[],
                lineno=node.right.lineno,
                col_offset=node.right.col_offset,
            )
            return self.visit(call)
        # Rewrite a >> b(...) as b(a, ...)
        args = 0 if isinstance(node.op, RShift) else len(node.right.args)
        node.right.args.insert(args, node.left)
        return self.visit(node.right)


def pipes(func_or_class: Callable) -> Callable:
    if isclass(func_or_class):
        ctx = stack()[1][0].f_locals
    else:
        ctx = func_or_class.__globals__

    # Extract AST
    source = getsource(func_or_class)
    tree = parse(dedent(source))

    # Remove the @pipes decorator and @pipes() decorators from the AST to avoid recursive calls
    tree.body[0].decorator_list = [
        d
        for d in tree.body[0].decorator_list
        if isinstance(d, Call)
        and d.func.id != "pipes"
        or isinstance(d, Name)
        and d.id != "pipes"
    ]

    # Update the AST and execute the new code
    tree = PipeTransformer().visit(tree)
    code = compile(
        tree, filename=(ctx["__file__"] if "__file__" in ctx else "repl"), mode="exec"
    )
    exec(code, ctx)
    return ctx[tree.body[0].name]


__all__ = ["pipes"]
