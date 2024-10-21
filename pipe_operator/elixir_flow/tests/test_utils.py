import ast
from unittest import TestCase

from pipe_operator.elixir_flow.utils import (
    node_contains_name,
    node_is_regular_BinOp,
    node_is_supported_operation,
    string_to_ast_BinOp,
)


class UtilsTestCase(TestCase):
    def test_string_to_ast_BinOp(self) -> None:
        # Test a few
        self.assertEqual(string_to_ast_BinOp(">>"), ast.RShift)
        self.assertEqual(string_to_ast_BinOp("/"), ast.Div)
        self.assertEqual(string_to_ast_BinOp("+"), ast.Add)
        # Expect crash if not a valid operator
        with self.assertRaises(ValueError):
            string_to_ast_BinOp("x")  # type: ignore

    def test_node_contains_name(self) -> None:
        # With basic nodes
        self.assertTrue(node_contains_name(ast.Name(id="x"), "x"))
        self.assertFalse(node_contains_name(ast.Name(id="x"), "y"))
        # With nested nodes
        node = ast.BinOp(left=ast.Name(id="x"), op=ast.RShift(), right=ast.Name(id="y"))
        self.assertTrue(node_contains_name(node, "x"))
        node = ast.BinOp(left=ast.Name(id="x"), op=ast.RShift(), right=ast.Name(id="y"))
        self.assertFalse(node_contains_name(node, "z"))

    def test_node_is_regular_BinOp(self) -> None:
        # With a BinOp
        node: ast.expr = ast.BinOp(
            left=ast.Name(id="x"), op=ast.RShift(), right=ast.Name(id="y")
        )
        self.assertFalse(node_is_regular_BinOp(node, ast.RShift))
        self.assertTrue(node_is_regular_BinOp(node, ast.Add))
        # With a non-BinOp
        node = ast.Name(id="x")
        self.assertFalse(node_is_regular_BinOp(node, ast.RShift))
        self.assertFalse(node_is_regular_BinOp(node, ast.Add))

    def test_node_is_supported_operation(self) -> None:
        # With a BinOp
        node: ast.expr = ast.BinOp(
            left=ast.Name(id="x"), op=ast.RShift(), right=ast.Name(id="y")
        )
        self.assertFalse(node_is_supported_operation(node, ast.RShift))
        self.assertTrue(node_is_supported_operation(node, ast.Add))
        # With a non-BinOp
        node = ast.Name(id="x")
        self.assertFalse(node_is_supported_operation(node, ast.Add))
        node = ast.List(elts=[ast.Name(id="x")])
        self.assertTrue(node_is_supported_operation(node, ast.Add))
