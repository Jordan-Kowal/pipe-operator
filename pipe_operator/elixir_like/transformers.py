import ast
from typing import Optional, Type

from pipe_operator.elixir_like.utils import (
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
        operator (OperatorString): The operator which will represent the pipe. Defaults to `>>`.
        placeholder (str): The placeholder variable used in method, attribute, and binary calls.
            Defaults to `_`.
        lambda_var (str): The variable name used in generated lambda functions when transforming
            binary operations. Useful to avoid overriding existing variables. Defaults to `Z`.
        debug_mode (bool): If true, will print the output after each pipe operation. Defaults to `False`.

    Raises:
        ValueError: If `placeholder` and `lambda_var` are the same.

    Examples:
        To transform a pipe-like list of instructions into a python-compatible one:

        >>> import ast
        >>> source_code = "3 >> Class >> _.attribute >> _.method(4) >> _ + 4 >> double() >> double(4) >> double >> (lambda x: x + 4)"
        >>> tree = ast.parse(source_code)

        Apply the `PipeTransformer` transformer:

        >>> replacer = PipeTransformer(
        >>>     operator=">>",
        >>>     placeholder="_",
        >>>     lambda_var="Z",
        >>>     debug_mode=False
        >>> )
        >>> transformed_tree = replacer.visit(tree)
        >>> ast.fix_missing_locations(transformed_tree)

        Convert the AST back to source code:

        >>> ast.unparse(transformed_tree)
        "(lambda x: x + 4)(double(double(double((lambda Z: Z + 4)(Class(3).attribute.method(4))), 4)))"
    """

    def __init__(
        self,
        operator: OperatorString = DEFAULT_OPERATOR,
        placeholder: str = DEFAULT_PLACEHOLDER,
        lambda_var: str = DEFAULT_LAMBDA_VAR,
        debug_mode: bool = False,
    ) -> None:
        # State
        self.operator: Type[ast.operator] = string_to_ast_BinOp(operator)
        self.placeholder = placeholder
        self.lambda_var = lambda_var
        self.debug_mode = debug_mode
        self.debug_func_node: Optional[ast.expr] = None
        # Computed
        self.lambda_transformer = ToLambdaTransformer(
            fallback_transformer=self,
            excluded_operator=self.operator,
            placeholder=placeholder,
            var_name=lambda_var,
        )
        if debug_mode:
            self.debug_func_node = self._create_debug_lambda()
        super().__init__()

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        # Exit early if not our pipe operator
        if not isinstance(node.op, self.operator):
            return node

        transformed_node = None

        # Property call `_.attribute`
        if (
            isinstance(node.right, ast.Attribute)
            and isinstance(node.right.value, ast.Name)
            and node.right.value.id == self.placeholder
        ):
            transformed_node = self._transform_attribute(node)
        # Method call `_.method(...)`
        elif (
            isinstance(node.right, ast.Call)
            and isinstance(node.right.func, ast.Attribute)
            and isinstance(node.right.func.value, ast.Name)
            and node.right.func.value.id == self.placeholder
        ):
            transformed_node = self._transform_method_call(node)
        # Direct operations like BinOp (but not our operator),
        # or List/Tuple/Set/Dict (and comprehensions)
        # or F-strings
        elif node_is_supported_operation(node.right, self.operator):
            transformed_node = self._transform_operation_to_lambda(node)
        # Lambda or function without parenthesis like `a >> b`
        elif not isinstance(node.right, ast.Call):
            transformed_node = self._transform_name_to_call(node)
        # Basic function/class call `a >> b(...)`
        else:
            transformed_node = self._transform_call(node)

        if self.debug_mode:
            transformed_node = self._add_debug(transformed_node)

        return transformed_node

    def _transform_attribute(self, node: ast.expr) -> ast.expr:
        """Rewrite `a >> _.property` as `a.property`."""
        attr = ast.Attribute(
            value=node.left,
            attr=node.right.attr,
            ctx=ast.Load(),
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(attr)

    def _transform_method_call(self, node: ast.expr) -> ast.Call:
        """Rewrite `a >> _.method(...)` as `a.method(...)`."""
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

    def _transform_operation_to_lambda(self, node: ast.expr) -> ast.expr:
        """Rewrites operations like `_ + 3` as `(lambda Z: Z + 3)`."""
        if not node_contains_name(node.right, self.placeholder):
            name = node.right.__class__.__name__
            raise RuntimeError(
                f"[PipeTransformer] `{name}` operation requires the `{self.placeholder}` variable at least once"
            )
        return self.lambda_transformer.visit(node)

    def _transform_name_to_call(self, node: ast.expr) -> ast.Call:
        """Rewrites `a >> b` as `b(a)`."""
        call = ast.Call(
            func=node.right,
            args=[node.left],
            keywords=[],
            lineno=node.right.lineno,
            col_offset=node.right.col_offset,
        )
        return self.visit(call)

    def _transform_call(self, node: ast.expr) -> ast.Call:
        """Rewrite `a >> b(...)` as `b(a, ...)`."""
        args = 0 if isinstance(node.op, self.operator) else len(node.right.args)
        node.right.args.insert(args, node.left)
        return self.visit(node.right)

    def _add_debug(self, node: ast.expr) -> ast.Call:
        """Updates the node so that it also prints the results before returning it."""
        return ast.Call(
            func=self.debug_func_node,
            args=[node],
            keywords=[],
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    @staticmethod
    def _create_debug_lambda() -> ast.expr:
        """Generates the AST for: `lambda x: (print(x), x)[1]`."""
        return ast.Lambda(
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="x", annotation=None, lineno=0, col_offset=0)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=ast.Subscript(
                value=ast.Tuple(
                    elts=[
                        ast.Call(
                            func=ast.Name(
                                id="print", ctx=ast.Load(), lineno=0, col_offset=0
                            ),
                            args=[
                                ast.Name(id="x", ctx=ast.Load(), lineno=0, col_offset=0)
                            ],
                            keywords=[],
                            lineno=0,
                            col_offset=0,
                        ),
                        ast.Name(id="x", ctx=ast.Load(), lineno=0, col_offset=0),
                    ],
                    ctx=ast.Load(),
                    lineno=0,
                    col_offset=0,
                ),
                slice=ast.Index(  # type: ignore
                    value=ast.Constant(value=1, lineno=0, col_offset=0),
                    lineno=0,
                    col_offset=0,
                ),
                ctx=ast.Load(),
                lineno=0,
                col_offset=0,
            ),
            lineno=0,
            col_offset=0,
        )


class ToLambdaTransformer(ast.NodeTransformer):
    """
    Transforms specific operations (like BinOp, List/Tuple/Set/Dict/F-string, or a comprehension)
    that use the `placeholder` variable into a 1-arg lambda function node that performs
    the same operation while also replacing the `placeholder` variable with `var_name`.
    Will crash if the operation does not contain the `placeholder` variable.

    Args:
        fallback_transformer (ast.NodeTransformer): The transformer to fallback on.
        excluded_operator (Type[ast.operator]): The operator to exclude.
            Defaults to `ast.RShift`.
        placeholder (str): The variable to be replaced.
            Defaults to `DEFAULT_PLACEHOLDER`.
        var_name (str): The variable name to use in our generated lambda functions.
            Defaults to `DEFAULT_LAMBDA_VAR`.

    Raises:
        ValueError: If `placeholder` and `var_name` are the same.

    Examples:
        To transformer operations into lambdas:

        >>> import ast
        >>> source_code = "1_000 >> _ + 3 >> double >> [_, 1, 2, [_, _]]"
        >>> tree = ast.parse(source_code)

        Apply the `LambdaTransformer` transformer:

        >>> replacer = LambdaTransformer(
        >>>     ast.NodeTransformer(),
        >>>     excluded_operator=ast.RShift,
        >>>     placeholder="_",
        >>>     var_name="Z",
        >>> )
        >>> transformed_tree = replacer.visit(tree)
        >>> ast.fix_missing_locations(transformed_tree)

        Convert the AST back to source code:

        >>> ast.unparse(transformed_tree)
        "1000 >> (lambda Z: Z + 3) >> double >> (lambda Z: [Z, 1, 2, [Z, Z]])"
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
        """Either transforms the current node into a lambda function or perform recursive visits."""
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
        """
        Creates a 1-arg lambda function that performs the operation of the original node,
        while also replacing the `placeholder` variable with the `var_name`
        (which is also the name of the lambda argument).
        """
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
    Transformer that recursively replaces `Name(id=target)` nodes
    with `Name(id=replacement)` nodes in the AST.

    Args:
        target (str): The id to search for. Defaults to `DEFAULT_PLACEHOLDER`.
        replacement (str): The id to replace with. Defaults to `DEFAULT_LAMBDA_VAR`.

    Raises:
        ValueError: If `target` and `replacement` are the same.

    Examples:
        To replace all occurrences of `_` with `Z` in a Python expression:

        >>> import ast
        >>> source_code = "1000 + _ + func(_) + _"
        >>> tree = ast.parse(source_code)

        Apply the `NameReplacer` transformer:

        >>> replacer = NameReplacer(target="_", replacement="Z")
        >>> transformed_tree = replacer.visit(tree)
        >>> ast.fix_missing_locations(transformed_tree)

        Convert the AST back to source code:

        >>> ast.unparse(transformed_tree)
        "1000 + Z + func(Z) + Z"
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
        """Maybe replaces the `Name(id=target)` node with `Name(id=replacement)."""
        if subnode.id != self.target:
            return subnode
        return ast.Name(
            id=self.replacement,
            ctx=ast.Load(),
            lineno=subnode.lineno,
            col_offset=subnode.col_offset,
        )
