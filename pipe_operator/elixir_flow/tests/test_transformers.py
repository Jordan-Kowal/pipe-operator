import ast
from unittest import TestCase
from unittest.mock import MagicMock

from pipe_operator.elixir_flow.transformers import (
    NameReplacer,
    PipeTransformer,
    ToLambdaTransformer,
)


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

    def test_classes(self) -> None:
        source = "3 >> Class"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "Class(3)")

    def test_attributes(self) -> None:
        source = "3 >> Class >> _.attribute"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "Class(3).attribute")

    def test_methods(self) -> None:
        source = "3 >> Class >> _.method(4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "Class(3).method(4)")

    def test_direct_operations(self) -> None:
        # BinOp
        source = "3 >> _ + 4 >> _ * _ + 3"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: Z * Z + 3)((lambda Z: Z + 4)(3))")
        # Dict
        source = "3 >> {1: _, '2': 2, _: 4}"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: {1: Z, '2': 2, Z: 4})(3)")
        # DictComp
        source = "3 >> {x: _ + _ for x in range(10)}"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: {x: Z + Z for x in range(10)})(3)")
        # GeneratorExp
        source = "3 >> (x + _ for x in range(10))"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: (x + Z for x in range(10)))(3)")
        # JoinedStr
        source_code = '3 >> f"something-{_}"'
        result = transform_code(source_code, self.transformer)
        self.assertEqual(result, "(lambda Z: f'something-{Z}')(3)")
        # List
        source = "3 >> [_, 3]"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: [Z, 3])(3)")
        # ListComp
        source = "3 >> [x + _ for x in range(10)]"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: [x + Z for x in range(10)])(3)")
        # Set
        source = "3 >> {_, 3}"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: {Z, 3})(3)")
        # SetComp
        source = "3 >> {x + _ for x in range(10)}"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: {x + Z for x in range(10)})(3)")
        # Tuple
        source = "3 >> (_, 3)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda Z: (Z, 3))(3)")

    def test_crash_on_direct_operation_missing_placeholder(self) -> None:
        with self.assertRaises(RuntimeError):
            source = "3 >> __ + 4"
            transform_code(source, self.transformer)

    def test_functions(self) -> None:
        source = "3 >> single >> double() >> triple(4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "triple(double(single(3)), 4)")

    def test_lambdas(self) -> None:
        source = "3 >> (lambda x: x + 4)"
        result = transform_code(source, self.transformer)
        self.assertEqual(result, "(lambda x: x + 4)(3)")

    def test_complex(self) -> None:
        source = (
            "3 "
            + ">> Class "
            + ">> _.attribute "
            + ">> _.method(4) "
            + ">> _ + 4 "
            + ">> double() "
            + ">> double(4) "
            + ">> double "
            + ">> (lambda x: x + 4) "
            + ">> [_, 4, {_: 1, 2: _}] "
            + ">> [x for x in range(len(_))]"
        )
        result = transform_code(source, self.transformer)
        self.assertEqual(
            result,
            "(lambda Z: [x for x in range(len(Z))])((lambda Z: [Z, 4, {Z: 1, 2: Z}])((lambda x: x + 4)(double(double(double((lambda Z: Z + 4)(Class(3).attribute.method(4))), 4)))))",
        )

    def test_with_custom_params(self) -> None:
        transformer = PipeTransformer(placeholder="__", lambda_var="XXX", operator="|")
        # The `>>` will not be replaced because we declared `|` as the operator
        source = (
            "3 "
            + "| Class "
            + "| __.attribute "
            + "| __.method(4) "
            + "| __ >> 4 "
            + "| double() "
            + "| double(4) "
            + "| double "
            + "| (lambda x: x + 4) "
            + "| [__, 4, {__: 1, 2: __}] "
            + "| [x for x in range(len(__))]"
        )
        result = transform_code(source, transformer)
        self.assertEqual(
            result,
            "(lambda XXX: [x for x in range(len(XXX))])((lambda XXX: [XXX, 4, {XXX: 1, 2: XXX}])((lambda x: x + 4)(double(double(double((lambda XXX: XXX >> 4)(Class(3).attribute.method(4))), 4)))))",
        )

    def test_with_debug_mode(self) -> None:
        transformer = PipeTransformer(debug_mode=True)
        source = "3 >> _ + 4 >> double"
        result = transform_code(source, transformer)
        self.assertEqual(
            result,
            "(lambda x: (print(x), x)[1])(double((lambda x: (print(x), x)[1])((lambda x: (print(x), x)[1])((lambda Z: Z + 4)(3)))))",
        )


class ToLambdaTransformerTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transformer = ToLambdaTransformer(ast.NodeTransformer())
        return super().setUpClass()

    def test_BinOp(self) -> None:
        source_code = "_ + 3"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: Z + 3"
        self.assertEqual(result, expected_result)

    def test_Dict(self) -> None:
        source_code = "{1: _, '2': 2, _: 4}"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: {1: Z, '2': 2, Z: 4}"
        self.assertEqual(result, expected_result)

    def test_DictComp(self) -> None:
        source_code = "{x: _ for x in range(4)}"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: {x: Z for x in range(4)}"
        self.assertEqual(result, expected_result)

    def test_GeneratorExp(self) -> None:
        source_code = "(x + 1 for x in range(_))"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: (x + 1 for x in range(Z))"
        self.assertEqual(result, expected_result)

    def test_JoinedStr(self) -> None:
        source_code = 'f"something-{_}"'
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: f'something-{Z}'"
        self.assertEqual(result, expected_result)

    def test_List(self) -> None:
        source_code = "[_, 3]"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: [Z, 3]"
        self.assertEqual(result, expected_result)

    def test_ListComp(self) -> None:
        source_code = "[x for x in range(_) if x % 2 == 0]"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: [x for x in range(Z) if x % 2 == 0]"
        self.assertEqual(result, expected_result)

    def test_Set(self) -> None:
        source_code = "{_, 3}"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: {Z, 3}"
        self.assertEqual(result, expected_result)

    def test_SetComp(self) -> None:
        source_code = "{x + _ for x in range(4)}"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: {x + Z for x in range(4)}"
        self.assertEqual(result, expected_result)

    def test_Tuple(self) -> None:
        source_code = "(_, 3)"
        result = transform_code(source_code, self.transformer)
        expected_result = "lambda Z: (Z, 3)"
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
        transformer = ToLambdaTransformer(
            fallback_transformer=fake_transformer,
            excluded_operator=ast.RShift,
            placeholder="_",
            var_name="Z",
        )
        # When missing variable
        source_code = "3 + 4"
        transform_code(source_code, transformer)
        # When BinOp is our pipe operator
        source_code = "3 >> 4"
        transform_code(source_code, transformer)
        self.assertEqual(fake_transformer.visit.call_count, 2)

    def test_does_not_change_unsupported_nodes(self) -> None:
        fake_transformer = MagicMock()
        fake_transformer.visit = MagicMock()
        transformer = ToLambdaTransformer(
            fallback_transformer=fake_transformer,
            excluded_operator=ast.RShift,
            placeholder="_",
            var_name="Z",
        )
        # Should not call the fallback nor change the source
        # It will called the unchanged transformer method
        source = "double(3)"
        result = transform_code(source, transformer)
        self.assertEqual(result, source)
        self.assertEqual(fake_transformer.visit.call_count, 0)


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
