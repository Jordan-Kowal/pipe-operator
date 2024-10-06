import ast
from inspect import getsource, isclass, stack
from textwrap import dedent
from typing import Any, Callable, TypeVar


class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Exit early if not `>>` operator
        if not isinstance(node.op, (ast.RShift)):
            return node
        # Property call `_.attribute`
        if (
            isinstance(node.right, ast.Attribute)
            and isinstance(node.right.value, ast.Name)
            and node.right.value.id == "_"
        ):
            return self.transform_attribute(node)
        # Method call `_.method(...)`
        if (
            isinstance(node.right, ast.Call)
            and isinstance(node.right.func, ast.Attribute)
            and isinstance(node.right.func.value, ast.Name)
            and node.right.func.value.id == "_"
        ):
            return self.transform_method_call(node)
        # Lambda or function without parenthesis
        if not isinstance(node.right, ast.Call):
            return self.transform_name_to_call(node)
        # Basic function call `a >> b(...)`
        return self.transform_pipe_operation(node)

    def transform_attribute(self, node: ast.expr) -> ast.expr:
        """Rewrite `a >> _.property` as `a.property`"""
        attr = ast.Attribute(
            value=node.left,
            attr=node.right.attr,
            ctx=ast.Load(),
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(attr)

    def transform_method_call(self, node: ast.expr) -> ast.Call:
        """Rewrite `a >> _.method(...)` as `a.method(...)`"""
        call = ast.Call(
            func=ast.Attribute(
                value=node.left,
                attr=node.right.func.attr,
                ctx=ast.Load(),
                lineno=node.right.func.lineno,
                col_offset=node.right.func.col_offset,
            ),
            args=node.right.args,
            keywords=node.right.keywords,
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(call)

    def transform_name_to_call(self, node: ast.expr) -> ast.Call:
        """Convert function name / lambda etc without braces into call"""
        call = ast.Call(
            func=node.right,
            args=[node.left],
            keywords=[],
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(call)

    def transform_pipe_operation(self, node: ast.expr) -> ast.Call:
        """Rewrite `a >> b(...)` as `b(a, ...)`"""
        args = 0 if isinstance(node.op, ast.RShift) else len(node.right.args)
        node.right.args.insert(args, node.left)
        return self.visit(node.right)


def pipes(func_or_class: Callable) -> Callable:
    if isclass(func_or_class):
        ctx = stack()[1][0].f_locals
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


T = TypeVar("T")


def tap(value: T, func_or_class: Callable[[T], Any]) -> T:
    func_or_class(value)
    return value


__all__ = ["pipes", "tap"]
