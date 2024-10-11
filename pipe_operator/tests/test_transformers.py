import ast
from unittest import TestCase
from unittest.mock import MagicMock

from pipe_operator.transformers import LambdaTransformer, NameReplacer


def transform_code(code_string: str, transformer: ast.NodeTransformer) -> str:
    tree = ast.parse(code_string)
    new_tree = transformer.visit(tree)
    return ast.unparse(new_tree)


class PipeTransformerTestCase(TestCase):
    pass


class LambdaTransformerTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transformer = LambdaTransformer(ast.NodeTransformer(), "_", "_pipe_x")

    def test_simple(self) -> None:
        source_code = "_ + 3"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda _pipe_x: _pipe_x + 3"
        self.assertEqual(result, expected_result)

    def test_should_ignore_right_shift(self) -> None:
        source_code = "100 >> _ + 3"
        result = transform_code(source_code, self.transformer)
        expected_result = "100 >> (lambda _pipe_x: _pipe_x + 3)"
        self.assertEqual(result, expected_result)

    def test_should_match_only_perfect_names(self) -> None:
        source_code = "_x + x_ + _x_ + _"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda _pipe_x: _x + x_ + _x_ + _pipe_x"
        self.assertEqual(result, expected_result)

    def test_complex(self) -> None:
        source_code = "1_000 >> _ + 3 >> double >> _ - _"
        result = transform_code(source_code, self.transformer)
        expected_result = "1000 >> (lambda _pipe_x: _pipe_x + 3) >> double >> (lambda _pipe_x: _pipe_x - _pipe_x)"
        self.assertEqual(result, expected_result)

    def test_should_fallback_on_parent(self) -> None:
        fake_transformer = MagicMock()
        fake_transformer.visit = MagicMock()
        transformer = LambdaTransformer(fake_transformer, "_", "_pipe_x")
        source_code = "3 + 4"
        transform_code(source_code, transformer)
        fake_transformer.visit.assert_called_once()


class NameReplacerTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transformer = NameReplacer("_", "_pipe_x")

    def test_correctly_replaces_names(self) -> None:
        source_code = "1000 + _ + func(_) + _"
        result = transform_code(source_code, self.transformer)
        expected_result = "1000 + _pipe_x + func(_pipe_x) + _pipe_x"
        self.assertEqual(result, expected_result)

    def test_no_change_if_no_match(self) -> None:
        source_code = "1_000 + _x + x_ + _x_"
        result = transform_code(source_code, self.transformer)
        expected_result = "1000 + _x + x_ + _x_"
        self.assertEqual(result, expected_result)

    def test_error_if_target_and_replacement_are_the_same(self) -> None:
        with self.assertRaises(ValueError):
            NameReplacer("_", "_")
