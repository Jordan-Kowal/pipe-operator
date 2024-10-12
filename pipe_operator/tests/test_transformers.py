import ast
from unittest import TestCase
from unittest.mock import MagicMock

from pipe_operator.transformers import LambdaTransformer, NameReplacer, PipeTransformer


def transform_code(code_string: str, transformer: ast.NodeTransformer) -> str:
    tree = ast.parse(code_string)
    new_tree = transformer.visit(tree)
    return ast.unparse(new_tree)


class PipeTransformerTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transformer = PipeTransformer()
        return super().setUpClass()

    def test_skip_if_not_rshift(self) -> None:
        source = "3 + 4 | double(x)"
        result = transform_code(source, self.transformer)
        self.assertEqual(source, result)

    def test_class(self) -> None:
        source = "3 >> Class"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "Class(3)")

    def test_attribute(self) -> None:
        source = "3 >> Class >> _.attribute"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "Class(3).attribute")

    def test_method(self) -> None:
        source = "3 >> Class >> _.method(4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "Class(3).method(4)")

    def test_binOp(self) -> None:
        source = "3 >> _ + 4 >> _ * _ + 3"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: Z * Z + 3)((lambda Z: Z + 4)(3))")

    def test_binOp_crash_on_missing_placeholder(self) -> None:
        with self.assertRaises(RuntimeError):
            source = "3 >> __ + 4"
            transform_code(source, self.transformer)

    def test_func(self) -> None:
        source = "3 >> double()"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "double(3)")

    def test_func_multiple_args(self) -> None:
        source = "3 >> double(4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "double(3, 4)")

    def test_func_without_parenthesis(self) -> None:
        source = "3 >> double"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "double(3)")

    def test_lambda(self) -> None:
        source = "3 >> (lambda x: x + 4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda x: x + 4)(3)")

    def test_complex(self) -> None:
        source = "3 >> Class >> _.attribute >> _.method(4) >> _ + 4 >> double() >> double(4) >> double >> (lambda x: x + 4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(
            result,
            "(lambda x: x + 4)(double(double(double((lambda Z: Z + 4)(Class(3).attribute.method(4))), 4)))",
        )

    def test_with_custom_params(self) -> None:
        transformer = PipeTransformer(placeholder="__", lambda_var="XXX", operator="|")
        # The `>>` will not be replaced because we declared `|` as the operator
        source = "3 | Class | __.attribute | __.method(4) | __ >> 4 | double() | double(4) | double | (lambda x: x + 4)"
        result = transform_code(source, transformer)
        self.assertEqual(
            result,
            "(lambda x: x + 4)(double(double(double((lambda XXX: XXX >> 4)(Class(3).attribute.method(4))), 4)))",
        )


class LambdaTransformerTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transformer = LambdaTransformer(ast.NodeTransformer())
        return super().setUpClass()

    def test_simple(self) -> None:
        source_code = "_ + 3"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: Z + 3"
        self.assertEqual(result, expected_result)

    def test_should_ignore_right_shift(self) -> None:
        source_code = "100 >> _ + 3"
        result = transform_code(source_code, self.transformer)
        expected_result = "100 >> (lambda Z: Z + 3)"
        self.assertEqual(result, expected_result)

    def test_should_match_only_perfect_names(self) -> None:
        source_code = "_x + x_ + _x_ + _"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: _x + x_ + _x_ + Z"
        self.assertEqual(result, expected_result)

    def test_complex(self) -> None:
        source_code = "1_000 >> _ + 3 >> double >> _ - _"
        result = transform_code(source_code, self.transformer)
        expected_result = "1000 >> (lambda Z: Z + 3) >> double >> (lambda Z: Z - Z)"
        self.assertEqual(result, expected_result)

    def test_should_fallback_on_parent(self) -> None:
        fake_transformer = MagicMock()
        fake_transformer.visit = MagicMock()
        transformer = LambdaTransformer(
            fallback_transformer=fake_transformer,
            operator=ast.RShift,
            placeholder="_",
            var_name="Z",
        )
        source_code = "3 + 4"
        transform_code(source_code, transformer)
        fake_transformer.visit.assert_called_once()


class NameReplacerTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transformer = NameReplacer()
        return super().setUpClass()

    def test_correctly_replaces_names(self) -> None:
        source_code = "1000 + _ + func(_) + _"
        result = transform_code(source_code, self.transformer)
        expected_result = "1000 + Z + func(Z) + Z"
        self.assertEqual(result, expected_result)

    def test_no_change_if_no_match(self) -> None:
        source_code = "1_000 + _x + x_ + _x_"
        result = transform_code(source_code, self.transformer)
        expected_result = "1000 + _x + x_ + _x_"
        self.assertEqual(result, expected_result)

    def test_error_if_target_and_replacement_are_the_same(self) -> None:
        with self.assertRaises(ValueError):
            NameReplacer("_", "_")
