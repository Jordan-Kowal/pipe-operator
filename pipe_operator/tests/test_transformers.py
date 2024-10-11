import ast
from unittest import TestCase

from pipe_operator.transformers import LambdaTransformer, NameReplacer


def transform_code(code_string: str, transformer: ast.NodeTransformer) -> str:
    tree = ast.parse(code_string)
    new_tree = transformer.visit(tree)
    return ast.unparse(new_tree)


class PipeTransformerTestCase(TestCase):
    pass


class LambdaTransformerTestCase(TestCase):
    def test_one(self) -> None:
        source_code = "1_000 >> _ + 3 >> double >> _ - _"
        transformer = LambdaTransformer(ast.NodeTransformer())
        result = transform_code(source_code, transformer)
        expected_result = "1000 >> (lambda _pipe_x: _pipe_x + 3) >> double >> (lambda _pipe_x: _pipe_x - _pipe_x)"
        self.assertEqual(result, expected_result)

    # Basic
    # Uses Parent
    # Does not impact >>
    # In name like _prout or prout_ or pr_out
    # Complex


class NameReplacerTestCase(TestCase):
    def test_correctly_replaces_names(self) -> None:
        source_code = "1000 + _ + func(_) + _"
        transformer = NameReplacer("_", "_pipe_x")
        result = transform_code(source_code, transformer)
        expected_result = "1000 + _pipe_x + func(_pipe_x) + _pipe_x"
        self.assertEqual(result, expected_result)

    def test_no_change_if_no_match(self) -> None:
        source_code = "1_000 + _x + x_ + _x_"
        transformer = NameReplacer("_", "_pipe_x")
        result = transform_code(source_code, transformer)
        expected_result = "1000 + _x + x_ + _x_"
        self.assertEqual(result, expected_result)

    def test_error_if_target_and_replacement_are_the_same(self) -> None:
        with self.assertRaises(ValueError):
            NameReplacer("_", "_")
