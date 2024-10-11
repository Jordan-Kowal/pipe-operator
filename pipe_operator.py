import ast
from inspect import getsource, isclass, stack
from textwrap import dedent
from typing import Any, Callable, TypeVar

PLACEHOLDER = "_"
LAMBDA_VAR = "pipe_x"


class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Exit early if not `>>` operator
        if not isinstance(node.op, ast.RShift):
            return node

        # Property call `_.attribute`
        if (
            isinstance(node.right, ast.Attribute)
            and isinstance(node.right.value, ast.Name)
            and node.right.value.id == PLACEHOLDER
        ):
            return self._transform_attribute(node)

        # Method call `_.method(...)`
        if (
            isinstance(node.right, ast.Call)
            and isinstance(node.right.func, ast.Attribute)
            and isinstance(node.right.func.value, ast.Name)
            and node.right.func.value.id == PLACEHOLDER
        ):
            return self._transform_method_call(node)

        # Binary operator instruction other than `>>`
        if (
            isinstance(node.right, ast.BinOp)
            and not isinstance(node.right.op, ast.RShift)
            and self._contains_underscore(node.right)
        ):
            return self._transform_operation_to_lambda(node)

        # Lambda or function without parenthesis
        if not isinstance(node.right, ast.Call):
            return self._transform_name_to_call(node)

        # Basic function call `a >> b(...)`
        return self._transform_pipe_operation(node)

    def _transform_attribute(self, node: ast.expr) -> ast.expr:
        """Rewrite `a >> _.property` as `a.property`"""
        attr = ast.Attribute(
            value=node.left,
            attr=node.right.attr,
            ctx=ast.Load(),
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(attr)

    def _transform_method_call(self, node: ast.expr) -> ast.Call:
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

    def _transform_operation_to_lambda(self, node: ast.expr) -> ast.AST:
        """Rewrites `_ + a + b - _` as `lambda pipe_x: pipe_x + a + b - pipe_x`"""
        transformer = LambdaTransformer(self)
        return transformer.visit(node)

    def _transform_name_to_call(self, node: ast.expr) -> ast.Call:
        """Convert function name / lambda etc without braces into call"""
        call = ast.Call(
            func=node.right,
            args=[node.left],
            keywords=[],
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(call)

    def _transform_pipe_operation(self, node: ast.expr) -> ast.Call:
        """Rewrite `a >> b(...)` as `b(a, ...)`"""
        args = 0 if isinstance(node.op, ast.RShift) else len(node.right.args)
        node.right.args.insert(args, node.left)
        return self.visit(node.right)

    @staticmethod
    def _contains_underscore(node: ast.expr) -> bool:
        """Checks if a node contains an underscore Name node"""
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Name) and subnode.id == "_":
                return True
        return False


class PlaceholderReplacer(ast.NodeTransformer):
    """Replaces all `_` with a lambda argument `x`."""

    def visit_Name(self, subnode: ast.expr) -> ast.expr:
        if subnode.id != PLACEHOLDER:
            return subnode
        return ast.Name(
            id=LAMBDA_VAR,
            ctx=ast.Load(),
            lineno=subnode.lineno,
            col_offset=subnode.col_offset,
        )


class LambdaTransformer(ast.NodeTransformer):
    def __init__(self, parent: ast.NodeTransformer) -> None:
        self.parent = parent
        super().__init__()

    def visit_BinOp(self, node: ast.expr) -> ast.expr:
        # If the operation contains `_` and is NOT a right-shift operation
        if self._contains_underscore(node) and not isinstance(node.op, ast.RShift):
            # Create a lambda function that replaces `_` with `x`
            return self._create_lambda(node)

        # Recursively visit all BinOp nodes in the AST
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        return self.parent.visit(node)

    def _contains_underscore(self, node: ast.expr) -> bool:
        """Checks if a node contains an underscore variable."""
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Name) and subnode.id == PLACEHOLDER:
                return True
        return False

    def _create_lambda(self, node: ast.expr) -> ast.Lambda:
        """Transforms the binary operation into a lambda function."""
        # Replace all occurrences of `_` with a lambda argument `x`
        replacer = PlaceholderReplacer()
        new_node = replacer.visit(node)

        # Create the lambda function: `lambda x: <new_node>`
        lambda_func = ast.Lambda(
            args=ast.arguments(
                args=[
                    ast.arg(
                        arg=LAMBDA_VAR,
                        annotation=None,
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                    )
                ],
                posonlyargs=[],
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=new_node,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        return lambda_func


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
