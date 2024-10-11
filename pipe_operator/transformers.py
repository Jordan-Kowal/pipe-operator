import ast

PLACEHOLDER = "_"
LAMBDA_VAR = "_pipe_x"


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


class LambdaTransformer(ast.NodeTransformer):
    """
    Changes a BinOp node (which is not a right shift operation)
    into a 1-arg lambda function that performs the same operation
    but replaces `_` with `_pipe_x`.

    Example:
        1_000 >> _ + 3 >> double >> _ - _
        1000 >> (lambda _pipe_x: _pipe_x + 3) >> double >> (lambda _pipe_x: _pipe_x - _pipe_x)
    """

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
        replacer = NameReplacer(PLACEHOLDER, LAMBDA_VAR)
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


class NameReplacer(ast.NodeTransformer):
    """
    In a Name node, replaces the id from `target` to `replacement`

    Example with target = "_", replacement = "x":
        "1000 + _ + func(_)"
        "1000 + x + func(x)"
    """

    def __init__(self, target: str, replacement: str) -> None:
        if target == replacement:
            raise ValueError("`target` and `replacement` must be different")
        self.target = target
        self.replacement = replacement
        super().__init__()

    def visit_Name(self, subnode: ast.expr) -> ast.expr:
        # Exit if not our target
        if subnode.id != self.target:
            return subnode
        # Replace `target` with `replacement`
        return ast.Name(
            id=self.replacement,
            ctx=ast.Load(),
            lineno=subnode.lineno,
            col_offset=subnode.col_offset,
        )
