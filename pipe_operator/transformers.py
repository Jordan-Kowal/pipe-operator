import ast
from typing import Type

from pipe_operator.utils import (
    OperatorString,
    node_contains_name,
    node_is_regular_BinOp,
    node_is_supported_operation,
    string_to_ast_BinOp,
)

DEFAULT_OPERATOR: OperatorString = ">>"
DEFAULT_PLACEHOLDER = "_"
DEFAULT_LAMBDA_VAR = "Z"


class PipeTransformer(ast.NodeTransformer):
    """
    Transform an elixir pipe-like list of instruction into a python-compatible one.

    It handles:
        class calls                         a >> B()                            B(a)
        method calls                        a >> _.method(...)                  a.method(...)
        property calls                      a >> _.property                     a.property
        binary operators                    a >> _ + 3                          (lambda Z: Z + 3)(a)
        f-strings                           a >> f"{_}"                         (lambda Z: f"{Z}")(a)
        list/set/... creations              a >> [_, 1, 2]                      (lambda Z: [Z, 1, 2])(a)
        list/set/... comprehensions         a >> [x + _ for x in range(_)]      (lambda Z: [x + Z for x in range(Z)])(a)
        function calls                      a >> b(...)                         b(a, ...)
        function calls w/o parenthesis      a >> b                              b(a)
        lambda calls                        a >> (lambda x: x + 4)              (lambda x: x + 4)(a)

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
        self.lambda_transformer = ToLambdaTransformer(
            fallback_transformer=self,
            excluded_operator=self.operator,
            placeholder=placeholder,
            var_name=lambda_var,
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

        # Direct operations like BinOp (but not our operator),
        # or List/Tuple/Set/Dict (and comprehensions)
        # or F-strings
        if node_is_supported_operation(node.right, self.operator):
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
        """Rewrites operations like `_ + 3` as `(lambda Z: Z + 3)`"""
        if not node_contains_name(node.right, self.placeholder):
            name = node.right.__class__.__name__
            raise RuntimeError(
                f"[PipeTransformer] `{name}` operation requires the `{self.placeholder}` variable at least once"
            )
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


class ToLambdaTransformer(ast.NodeTransformer):
    """
    Transforms specific operations (like BinOp, List/Tuple/Set/Dict/F-string, or a comprehension)
    that use the `placeholder` variable into a 1-arg lambda function node
    that performs the same operation while also replacing the `placeholder` variable with `var_name`.
    Will crash if the operation does not contain the `placeholder` variable.

    Args:
        fallback_transformer:   The transformer to use if the operation is not supported
        excluded_operator:      The operator to exclude (because this is our pipe operator)
        placeholder:            The variable to be replaced
        var_name:               The variable name to use in our generated lambda functions

    Usage:
        ```
        LambdaTransformer(
            ast.NodeTransformer(),
            excluded_operator=ast.RShift,
            placeholder="_",
            var_name="Z",
        )

        1_000 >> _ + 3 >> double >> _ - _
        1000 >> (lambda Z: Z + 3) >> double >> (lambda Z: Z - Z)

        1_000 >> _ + 3 >> [_, 1, 2, [_, _]]
        1000 >> (lambda Z: Z + 3) >> (lambda Z: [Z, 1, 2, [Z, Z]])
        ```
    """

    def __init__(
        self,
        fallback_transformer: ast.NodeTransformer,
        excluded_operator: Type[ast.operator] = ast.RShift,
        placeholder: str = DEFAULT_PLACEHOLDER,
        var_name: str = DEFAULT_LAMBDA_VAR,
    ) -> None:
        self.fallback_transformer = fallback_transformer
        self.excluded_operator = excluded_operator
        self.placeholder = placeholder
        self.var_name = var_name
        self.name_transformer = NameReplacer(placeholder, var_name)
        super().__init__()

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        return self._transform(node)

    def visit_Dict(self, node: ast.Dict) -> ast.AST:
        return self._transform(node)

    def visit_DictComp(self, node: ast.DictComp) -> ast.AST:
        return self._transform(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> ast.AST:
        return self._transform(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        return self._transform(node)

    def visit_List(self, node: ast.List) -> ast.AST:
        return self._transform(node)

    def visit_ListComp(self, node: ast.ListComp) -> ast.AST:
        return self._transform(node)

    def visit_Set(self, node: ast.Set) -> ast.AST:
        return self._transform(node)

    def visit_SetComp(self, node: ast.SetComp) -> ast.AST:
        return self._transform(node)

    def visit_Tuple(self, node: ast.Tuple) -> ast.AST:
        return self._transform(node)

    def _transform(self, node: ast.expr) -> ast.AST:
        """Maybe transforms the operation into a lambda function or perform recursive visit"""
        is_not_BinOp = not isinstance(node, ast.BinOp)
        is_valid_BinOp = node_is_regular_BinOp(node, self.excluded_operator)
        if (is_not_BinOp or is_valid_BinOp) and node_contains_name(
            node, self.placeholder
        ):
            return self._to_lambda(node)
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        return self.fallback_transformer.visit(node)

    def _to_lambda(self, node: ast.expr) -> ast.Lambda:
        """Transforms the operation into a lambda function"""
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

    Args:
        target:         The id to be replaced
        replacement:    The id to replace the target

    Usage:
        ```
        NameReplacer("_", "x")
        "1000 + _ + func(_)"
        "1000 + x + func(x)"
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

    def visit_Name(self, subnode: ast.Name) -> ast.Name:
        """Replaces the Name node with a new one if necessary"""
        if subnode.id != self.target:
            return subnode
        return ast.Name(
            id=self.replacement,
            ctx=ast.Load(),
            lineno=subnode.lineno,
            col_offset=subnode.col_offset,
        )