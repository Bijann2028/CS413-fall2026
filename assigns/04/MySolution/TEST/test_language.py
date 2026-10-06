import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lambda1 as L
from backend import LambdaBackend
from reader import InputError, read_source
from worker import perform


class FreeVariablesTests(unittest.TestCase):
    def test_every_expression_form(self):
        x, y, z = L.D0Evar("x"), L.D0Evar("y"), L.D0Evar("z")
        cases = [
            (L.D0Eint(1), set()), (L.D0Ebtf(True), set()), (x, {"x"}),
            (L.D0Eop1("+1", x), {"x"}), (L.D0Eop2("+", x, y), {"x", "y"}),
            (L.D0Elam("x", L.D0Epair(x, y)), {"y"}),
            (L.D0Efix("x", "y", L.D0Epair(x, L.D0Epair(y, z))), {"z"}),
            (L.D0Eapp(x, y), {"x", "y"}),
            (L.D0Eif0(x, y, z), {"x", "y", "z"}),
            (L.D0Elet("x", y, L.D0Epair(x, z)), {"y", "z"}),
            (L.D0Epair(x, y), {"x", "y"}),
            (L.D0Epfst(x), {"x"}), (L.D0Epsnd(y), {"y"}),
        ]
        for expression, expected in cases:
            with self.subTest(constructor=type(expression).__name__):
                found = L.d0exp_fvset(expression)
                self.assertIsInstance(found, frozenset)
                self.assertEqual(found, frozenset(expected))

    def test_duplicates_nested_scope_unused_bindings_and_let_initializer(self):
        cases = {
            'D0Epair(D0Evar("x"), D0Evar("x"))': {"x"},
            'D0Elam("x", D0Elam("y", D0Epair(D0Evar("x"), D0Evar("y"))))': set(),
            'D0Elam("unused", D0Eint(1))': set(),
            'D0Elet("x", D0Evar("x"), D0Evar("x"))': {"x"},
            'D0Elet("x", D0Eint(1), D0Elam("x", D0Evar("x")))': set(),
            'D0Efix("f", "x", D0Eapp(D0Evar("f"), D0Evar("x")))': set(),
            'D0Eif0(D0Ebtf(True), D0Eint(0), D0Evar("unused_branch"))': {"unused_branch"},
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(L.d0exp_fvset(read_source(source)), frozenset(expected))
        with self.assertRaises(TypeError):
            L.d0exp_fvset(L.D0E000())


class ReaderTests(unittest.TestCase):
    def test_nested_comments_multiline_and_signed_integer(self):
        source = '# a comment\nD0Eop2("+",\n D0Eint(-2), # inline\n D0Eint(+44)\n)'
        self.assertEqual(L.d0exp_evaluate(read_source(source)), L.D0Vint(42))

    def test_rejects_unsafe_syntax_bad_arity_and_bad_types(self):
        sources = ["", "  ", "42", "D0Eint(True)", "D0Ebtf(1)", 'D0Evar(4)',
                   "D0Eint()", "D0Eint(arg1=1)", "D0Eint(1,2)", "D0Eint(1+2)",
                   "D0Eint(*[1])", "D0E000()", "D0Vint(1)", "lambda1.D0Eint(1)",
                   "__import__('os').system('echo unsafe')", "D0Eint(1); D0Eint(2)",
                   "[D0Eint(1)]", "(D0Eint(1) for i in [])", "D0Eint(1.5)",
                   'D0Eop2("+", 1, D0Eint(2))', "D0Eint("]
        for source in sources:
            with self.subTest(source=source), self.assertRaises(InputError):
                read_source(source)

    def test_bounds(self):
        with self.assertRaises(InputError):
            read_source("#" + "x" * 65536 + "\nD0Eint(1)")
        with self.assertRaises(InputError):
            read_source('D0Eop1("+1",' * 101 + "D0Eint(1)" + ")" * 101)


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.backend = LambdaBackend()

    def test_lint_closed_open_sorted_frozenset_and_no_evaluation(self):
        with patch.object(L, "d0exp_evaluate", side_effect=AssertionError("Lint evaluated!")):
            result = perform("lint", 'D0Eop2("/", D0Eint(1), D0Eint(0))')
            self.assertEqual(result["outcome"], "success")
        result = self.backend.lint('D0Epair(D0Evar("z"), D0Evar("a"))', 7)
        self.assertEqual((result.operation, result.revision, result.outcome), ("lint", 7, "language_error"))
        self.assertEqual(result.text, "Undeclared variables: a, z")
        self.assertIsInstance(result.free_variables, frozenset)
        self.assertEqual(result.free_variables, frozenset({"a", "z"}))
        self.assertEqual(self.backend.lint("D0Eint(42)", 1).outcome, "success")

    def test_real_arithmetic_factorial_and_fibonacci_base_cases(self):
        arithmetic = self.backend.interpret('D0Eop2("+", D0Eint(20), D0Eint(22))', 3)
        self.assertEqual((arithmetic.outcome, arithmetic.text), ("success", "D0Vint(arg1=42)"))
        for name, inputs in [("factorial", [(5, 120), (0, 1), (1, 1)]),
                             ("fibonacci", [(10, 55), (0, 0), (1, 1)])]:
            source = (ROOT / "samples" / f"{name}.lambda").read_text(encoding="utf-8")
            # Replace only the final application argument, retaining the real recursive body.
            expression = read_source(source)
            self.assertIsInstance(expression, L.D0Eapp)
            for argument, expected in inputs:
                with self.subTest(example=name, argument=argument):
                    tree = ast.parse(source, mode="eval")
                    tree.body.args[1] = ast.Call(func=ast.Name(id="D0Eint", ctx=ast.Load()),
                                               args=[ast.Constant(argument)], keywords=[])
                    result = self.backend.interpret(ast.unparse(tree), 4)
                    self.assertEqual((result.outcome, result.text), ("success", f"D0Vint(arg1={expected})"))

    def test_input_and_runtime_errors_and_nested_sentinels(self):
        self.assertEqual(self.backend.interpret('D0Eint("bad")', 1).outcome, "input_error")
        for source in ['D0Eop2("/",D0Eint(1),D0Eint(0))', 'D0Evar("x")',
                       'D0Epair(D0Eint(1),D0Epair(D0Eint(2),D0Evar("x")))',
                       'D0Eapp(D0Eint(1), D0Eint(2))', 'D0Epfst(D0Eint(1))',
                       'D0Eop2("unknown",D0Eint(1),D0Eint(2))']:
            with self.subTest(source=source):
                self.assertEqual(self.backend.interpret(source, 1).outcome, "runtime_error")

    def test_placeholders_and_no_artifact(self):
        for operation in ("typecheck", "compile"):
            result = getattr(self.backend, operation)("D0Eint(1)", 2)
            self.assertEqual(result.outcome, "not_implemented")
            self.assertIsNone(result.artifact)

    def test_real_timeout_and_retry(self):
        # The recursive program is finite but too expensive to finish in the limit.
        source = (ROOT / "samples" / "fibonacci.lambda").read_text(encoding="utf-8").replace("D0Eint(10)", "D0Eint(40)")
        backend = LambdaBackend(timeout=0.1)
        self.assertEqual(backend.interpret(source, 1).outcome, "timeout")
        backend.timeout = 3
        self.assertEqual(backend.interpret("D0Eint(42)", 1).text, "D0Vint(arg1=42)")

    def test_backend_launch_failure(self):
        with patch("backend.subprocess.run", side_effect=OSError("worker unavailable")):
            self.assertEqual(self.backend.lint("D0Eint(1)", 1).outcome, "backend_error")


if __name__ == "__main__":
    unittest.main()
