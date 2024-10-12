import ast
from typing import Type

from pipe_operator.utils import OperatorString, node_contains_name, string_to_ast_BinOp

DEFAULT_OPERATOR: OperatorString = ">>"
DEFAULT_PLACEHOLDER = "_"
DEFAULT_LAMBDA_VAR = "Z"


class PipeTransformer(ast.NodeTransformer):
    """
    Transform an elixir pipe-like list of instruction into a python-compatible one.

    It handles:
        class calls                         a >> B()                 B(a)
        method calls                        a >> _.method(...)       a.method(...)
        property calls                      a >> _.property          a.property
        binary operators                    a >> _ + 3               (lambda Z: Z + 3)(a)
        function calls                      a >> b(...)              b(a, ...)
        function calls w/o parenthesis      a >> b                   b(a)
        lambda calls                        a >> (lambda x: x + 4)   (lambda x: x + 4)(a)

    Args:
        operator:       The operator which will represent the pipe. Must be a valid python operator. Defaults to `>>`.
        placeholder:    The placeholder variable used in method, attribute, and binary calls. Defaults to `_`.
        lambda_var:     The variable name used in generated lambda functions when transforming binary operations.
                        Useful to avoid overriding existing variables. Defaults to `Z`.

    Usage:
        ```
        PipeTransformer()

        3 >> double >> Class
        Class(double(3))

        (
            3
            >> Class
            >> _.attribute
            >> _.method(4)
            >> _ + 4
            >> double()
            >> double(4)
            >> double
            >> (lambda x: x + 4)
        )
        (lambda x: x + 4)(
            double(double(double((lambda Z: Z + 4)(Class(3).attribute.method(4))), 4))
        )
        ```
    """

    def __init__(
        self,
        operator: OperatorString = DEFAULT_OPERATOR,
        placeholder: str = DEFAULT_PLACEHOLDER,
        lambda_var: str = DEFAULT_LAMBDA_VAR,
    ) -> None:
        self.operator: Type[ast.operator] = string_to_ast_BinOp(operator)
        self.placeholder = placeholder
        self.lambda_var = lambda_var
        self.lambda_transformer = LambdaTransformer(
            self, self.operator, placeholder, lambda_var
        )
        super().__init__()

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Exit early if not our pipe operator
        if not isinstance(node.op, self.operator):
            return node

        # Property call `_.attribute`
        if (
            isinstance(node.right, ast.Attribute)
            and isinstance(node.right.value, ast.Name)
            and node.right.value.id == self.placeholder
        ):
            return self._transform_attribute(node)

        # Method call `_.method(...)`
        if (
            isinstance(node.right, ast.Call)
            and isinstance(node.right.func, ast.Attribute)
            and isinstance(node.right.func.value, ast.Name)
            and node.right.func.value.id == self.placeholder
        ):
            return self._transform_method_call(node)

        # Binary operator instruction other than our pipe operator
        # Will crash if does not have the placeholder
        if isinstance(node.right, ast.BinOp) and not isinstance(
            node.right.op, self.operator
        ):
            if not node_contains_name(node.right, self.placeholder):
                raise RuntimeError(
                    f"[PipeTransformer] BinOp requires the `{self.placeholder}` variable at least once"
                )
            return self._transform_operation_to_lambda(node)

        # Lambda or function without parenthesis
        if not isinstance(node.right, ast.Call):
            return self._transform_name_to_call(node)

        # Basic function/class call `a >> b(...)`
        return self._transform_call(node)

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
        """Rewrites `_ + a + b - _` as `lambda X: X + a + b - X`"""
        return self.lambda_transformer.visit(node)

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

    def _transform_call(self, node: ast.expr) -> ast.Call:
        """Rewrite `a >> b(...)` as `b(a, ...)`"""
        args = 0 if isinstance(node.op, self.operator) else len(node.right.args)
        node.right.args.insert(args, node.left)
        return self.visit(node.right)


class LambdaTransformer(ast.NodeTransformer):
    """
    If the node is a BinOp (but not our pipe operator) and contains the placeholder variable,
    it changes it into a 1-arg lambda function node that performs the same operation
    and also replaces the `placeholder` variable with `var_name`

    Usage:
        ```
        LambdaTransformer("_", "Z")
        1_000 >> _ + 3 >> double >> _ - _
        1000 >> (lambda Z: Z + 3) >> double >> (lambda Z: Z - Z)
        ```
    """

    def __init__(
        self,
        fallback_transformer: ast.NodeTransformer,
        operator: Type[ast.operator] = ast.RShift,
        placeholder: str = DEFAULT_PLACEHOLDER,
        var_name: str = DEFAULT_LAMBDA_VAR,
    ) -> None:
        self.fallback_transformer = fallback_transformer
        self.operator = operator
        self.placeholder = placeholder
        self.var_name = var_name
        self.name_transformer = NameReplacer(placeholder, var_name)
        super().__init__()

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Changes the BinOp node into a lambda node if necessary"""
        # Maybe change the operation
        if not isinstance(node.op, self.operator) and node_contains_name(
            node, self.placeholder
        ):
            return self._create_lambda(node)
        # Recursively visit all BinOp nodes in the AST
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        return self.fallback_transformer.visit(node)

    def _create_lambda(self, node: ast.BinOp) -> ast.Lambda:
        """Transforms the binary operation into a lambda function"""
        new_node = self.name_transformer.visit(node)
        return ast.Lambda(
            args=ast.arguments(
                args=[
                    ast.arg(
                        arg=self.var_name,
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


class NameReplacer(ast.NodeTransformer):
    """
    In a Name node, replaces the id from `target` to `replacement`

    Usage:
        ```
        NameReplacer("_", "x")
        In: "1000 + _ + func(_)"
        Out: "1000 + x + func(x)"
        ```
    """

    def __init__(
        self, target: str = DEFAULT_PLACEHOLDER, replacement: str = DEFAULT_LAMBDA_VAR
    ) -> None:
        if target == replacement:
            raise ValueError("`target` and `replacement` must be different")
        self.target = target
        self.replacement = replacement
        super().__init__()

    def visit_Name(self, subnode: ast.expr) -> ast.expr:
        """Replaces the Name node with a new one if necessary"""
        if subnode.id != self.target:
            return subnode
        return ast.Name(
            id=self.replacement,
            ctx=ast.Load(),
            lineno=subnode.lineno,
            col_offset=subnode.col_offset,
        )
