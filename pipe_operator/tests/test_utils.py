import ast
from unittest import TestCase

from pipe_operator.utils import node_contains_name, string_to_ast_BinOp


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
        op = ast.BinOp(left=ast.Name(id="x"), op=ast.RShift(), right=ast.Name(id="y"))
        self.assertTrue(node_contains_name(op, "x"))
        op = ast.BinOp(left=ast.Name(id="x"), op=ast.RShift(), right=ast.Name(id="y"))
        self.assertFalse(node_contains_name(op, "z"))
