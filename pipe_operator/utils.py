import ast
from typing import Literal, Type

OperatorString = Literal[
    "+", "-", "*", "/", "%", "**", "<<", ">>", "|", "^", "&", "//", "@"
]

AST_STRING_MAP: dict[OperatorString, Type[ast.operator]] = {
    "+": ast.Add,
    "-": ast.Sub,
    "*": ast.Mult,
    "/": ast.Div,
    "%": ast.Mod,
    "**": ast.Pow,
    "<<": ast.LShift,
    ">>": ast.RShift,
    "|": ast.BitOr,
    "^": ast.BitXor,
    "&": ast.BitAnd,
    "//": ast.FloorDiv,
    "@": ast.MatMult,
}


def string_to_ast_BinOp(value: OperatorString) -> Type[ast.operator]:
    """Converts a string to an ast.BinOp"""
    if value not in AST_STRING_MAP:
        raise ValueError(f"Invalid operator: {value}")
    return AST_STRING_MAP[value]


def node_contains_name(node: ast.expr, name: str) -> bool:
    """Checks if a node contains a Name(id=`name`) node"""
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name) and subnode.id == name:
            return True
    return False
