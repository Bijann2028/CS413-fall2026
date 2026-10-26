import copy
import itertools
import unittest
from unittest.mock import patch

from MySolution import church, compiler, evaluator
from MySolution.compiler import compile_expr, CompilationError
from MySolution.evaluator import evaluate, source_data, EvaluationError
from MySolution.examples import required_examples, loop, factorial, fibonacci
from MySolution.observe import observe, PairKind
from MySolution.source import (
    D0ExpVisitor, D0Eint as N, D0Ebtf as B, D0Evar as V, D0Elam as L,
    D0Eapp as A, D0Efix as F, D0Eop1 as U, D0Eop2 as O, D0Eif0 as If,
    D0Elet as Let, D0Epair as Pair, D0Epfst as Fst, D0Epsnd as Snd, d0exp_fvset,
)
from MySolution.source_ops import substitute_source, format_source
from MySolution.terms import Var, Lam, App, free_variables, format_term, walk


class CompilerTests(unittest.TestCase):
    def check(self, expression, expected, kind=None):
        if kind is None:
            kind = "bool" if type(expected) is bool else "nat"
        snapshot = copy.deepcopy(expression)
        source = evaluate(expression)
        self.assertTrue(source.completed)
        self.assertEqual(source_data(source.value), expected)
        target = compile_expr(expression)
        self.assertEqual(free_variables(target), d0exp_fvset(expression))
        result = evaluate(target, 20_000)
        self.assertTrue(result.completed)
        observed = observe(result.value, kind, 10_000)
        self.assertEqual(observed.status, "completed", observed.message)
        self.assertIs(type(observed.value), type(expected))
        self.assertEqual(observed.value, expected)
        self.assertEqual(expression, snapshot)

    def test_all_required_demonstrations(self):
        for example in required_examples():
            with self.subTest(name=example.name):
                if example.exhausts:
                    result = evaluate(compile_expr(example.expression), example.execution_budget)
                    self.assertEqual((result.status, result.steps), ("exhausted", example.execution_budget))
                else:
                    self.check(example.expression, example.expected, example.kind)

    def test_zero_and_both_boolean_literals(self):
        self.check(N(0), 0)
        self.check(B(True), True)
        self.check(B(False), False)

    def test_all_required_operators(self):
        cases = [("+", 2, 3, 5), ("-", 2, 3, 0), ("-", 3, 2, 1), ("*", 3, 2, 6)]
        comparisons = {
            "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
        }
        for op, expected in comparisons.items():
            for a, b in [(0, 0), (1, 2), (2, 1), (2, 2)]:
                cases.append((op, a, b, expected(a, b)))
        for op, a, b, expected in cases:
            with self.subTest(op=op, a=a, b=b):
                self.check(O(op, N(a), N(b)), expected)
        for a, b in itertools.product((False, True), repeat=2):
            with self.subTest(a=a, b=b):
                self.check(O("and", B(a), B(b)), a and b)
                self.check(O("or", B(a), B(b)), a or b)
        for a in (False, True):
            self.check(U("not", B(a)), not a)

    def test_lexical_scope_and_let_initializer(self):
        self.check(Let("x", N(2), Let("x", O("+", V("x"), N(1)), V("x"))), 3)
        self.check(Let("x", N(2), A(L("x", V("x")), N(9))), 9)
        self.check(Let("x", N(2), Let("f", L("y", O("+", V("x"), V("y"))),
                                       Let("x", N(99), A(V("f"), N(3))))), 5)

    def test_each_fix_binder_and_coincident_binders(self):
        self.check(A(F("f", "f", V("f")), N(3)), 3)
        self.check(Let("f", N(99), A(F("f", "x", V("x")), N(4))), 4)
        self.check(Let("x", N(99), A(F("f", "x", V("x")), N(4))), 4)
        self.check(A(F("f", "x", A(L("f", V("f")), V("x"))), N(6)), 6)
        self.check(factorial(0), 1)
        self.check(factorial(3), 6)
        self.check(fibonacci(0), 0)
        self.check(fibonacci(1), 1)

    def test_recursive_functions_return_values_before_application(self):
        expression = F("loop", "x", A(V("loop"), V("x")))
        source = evaluate(expression)
        self.assertIsInstance(source.value, F)
        target = evaluate(compile_expr(expression), 10)
        self.assertTrue(target.completed)
        self.assertIsInstance(target.value, Lam)

    def test_open_expressions_free_variables_and_common_encoding_names(self):
        for name in ("s", "z", "t", "f", "x", "p", "u", "v", "thunk_1", "thunk_2"):
            cases = [V(name), L("other", V(name)), If(B(True), V(name), N(0)),
                     Let(name, V(name), V(name)), Pair(V(name), B(True)),
                     F("recursive", "argument", A(V(name), V("argument")))]
            for expression in cases:
                with self.subTest(name=name, expression=expression):
                    snapshot = copy.deepcopy(expression)
                    target = compile_expr(expression)
                    self.assertEqual(free_variables(target), d0exp_fvset(expression))
                    self.assertEqual(expression, snapshot)
                    self.assertEqual(target, compile_expr(expression))
        for expression in [F("f", "x", O("+", V("f"), V("free"))),
                           F("f", "x", O("+", V("x"), V("free"))),
                           F("same", "same", V("same"))]:
            self.assertEqual(free_variables(compile_expr(expression)), d0exp_fvset(expression))

    def test_generated_binders_do_not_capture_deliberate_collisions(self):
        for name in ("s", "z", "t", "f", "x", "thunk_1", "thunk_2"):
            with self.subTest(name=name):
                self.check(Let(name, N(8), If(B(True), V(name), N(0))), 8)
                self.check(A(L(name, O("+", V(name), N(1))), N(2)), 3)

    def test_open_execution_is_documentedly_rejected(self):
        expression = Let("x", V("x"), V("x"))
        self.assertEqual(free_variables(compile_expr(expression)), {"x"})
        with self.assertRaisesRegex(EvaluationError, "closed"):
            evaluate(compile_expr(expression), 20)
        with self.assertRaisesRegex(EvaluationError, "closed"):
            evaluate(expression)

    def test_both_conditional_outcomes_and_short_circuiting_skip_divergence(self):
        cases = [(If(B(True), N(1), loop()), 1),
                 (If(B(False), loop(), N(2)), 2),
                 (O("and", B(False), loop()), False),
                 (O("or", B(True), loop()), True)]
        for expression, expected in cases:
            with self.subTest(expression=expression):
                self.check(expression, expected)

    def test_strict_contexts_and_selected_branches_exhaust(self):
        cases = [A(L("x", N(0)), loop()), Let("x", loop(), N(2)),
                 Fst(Pair(N(2), loop())), Snd(Pair(loop(), B(True))),
                 Fst(Pair(loop(), N(2))), Snd(Pair(B(True), loop())),
                 If(B(True), loop(), N(1)), If(B(False), N(1), loop()),
                 O("and", B(True), loop()), O("or", B(False), loop()),
                 O("+", N(0), loop()), O("*", loop(), N(0))]
        for expression in cases:
            with self.subTest(expression=expression):
                result = evaluate(compile_expr(expression), 100)
                self.assertEqual((result.status, result.steps), ("exhausted", 100))

    def test_nested_pairs_and_functions_returning_pairs(self):
        nested = Pair(Pair(N(2), B(True)), N(3))
        self.check(nested, ((2, True), 3), PairKind(PairKind("nat", "bool"), "nat"))
        self.check(A(L("x", Fst(V("x"))), Pair(N(7), B(False))), 7)
        self.check(Let("p", Pair(N(4), N(5)), Snd(V("p"))), 5)

    def test_unsupported_forms_are_rejected_throughout_the_ast(self):
        bad_forms = [(N(-1), "-1"), (O("/", N(4), N(2)), "/"),
                     (U("+1", N(1)), "+1"), (O("&&", B(True), B(False)), "&&")]
        wrappers = [lambda e: e, lambda e: If(B(True), N(1), e),
                    lambda e: L("x", e), lambda e: F("f", "x", e),
                    lambda e: O("and", B(False), e), lambda e: Pair(N(0), e)]
        for (bad, diagnostic), wrap in itertools.product(bad_forms, wrappers):
            with self.subTest(bad=bad, wrapper=wrap):
                with self.assertRaises(CompilationError) as caught:
                    compile_expr(wrap(bad))
                self.assertIn(diagnostic, str(caught.exception))

    def test_compilation_is_pure_compositional_and_never_calls_evaluation(self):
        self.assertTrue(issubclass(compiler.Compiler, D0ExpVisitor))
        with patch.object(evaluator, "evaluate", side_effect=AssertionError("compiler evaluated source")):
            for expression in (O("+", N(2), N(3)), loop(), L("x", V("x"))):
                snapshot = copy.deepcopy(expression)
                target = compile_expr(expression)
                self.assertTrue(all(type(node) in (Var, Lam, App) for node in walk(target)))
                self.assertEqual(expression, snapshot)
        self.assertEqual(compile_expr(A(V("f"), V("x"))), App(Var("f"), Var("x")))
        self.assertEqual(compile_expr(L("x", V("x"))), Lam("x", Var("x")))

    def test_target_execution_uses_no_source_arithmetic_or_substitution(self):
        target = compile_expr(O("+", N(2), N(3)))
        with patch.object(evaluator, "_source_binary", side_effect=AssertionError("source arithmetic used")), \
             patch.object(evaluator, "substitute_source", side_effect=AssertionError("source substitution used")):
            execution = evaluate(target, 100)
            self.assertEqual(observe(execution.value, "nat", 100).value, 5)


class SourceOperationsTests(unittest.TestCase):
    def test_source_substitution_captures_neither_fix_binder(self):
        for binder in ("f", "arg"):
            expression = F("f", "arg", Pair(V("target"), V(binder)))
            replacement = V(binder)
            snapshot = copy.deepcopy((expression, replacement))
            result = substitute_source(expression, "target", replacement)
            self.assertEqual(d0exp_fvset(result), {binder})
            self.assertNotEqual(result.arg1 if binder == "f" else result.arg2, binder)
            self.assertEqual((expression, replacement), snapshot)

    def test_source_coincident_binders_and_let_initializer_scope(self):
        expression = F("same", "same", V("target"))
        result = substitute_source(expression, "target", V("same"))
        self.assertEqual(result.arg1, result.arg2)
        self.assertEqual(d0exp_fvset(result), {"same"})
        let = substitute_source(Let("x", V("x"), V("x")), "x", N(3))
        self.assertEqual(let, Let("x", N(3), V("x")))

    def test_source_application_pair_and_arithmetic_order(self):
        cases = [
            (A(A(L("function", V("function")), L("outer", V("outer"))),
               A(L("argument", V("argument")), N(4))), ["function", "argument", "outer"]),
            (Pair(A(L("left", V("left")), N(1)), A(L("right", V("right")), N(2))), ["left", "right"]),
            (O("+", A(L("left", V("left")), N(1)), A(L("right", V("right")), N(2))), ["left", "right"]),
        ]
        for expression, expected in cases:
            trace = []
            evaluate(expression, on_beta=lambda fn, arg: trace.append(fn.arg1))
            self.assertEqual(trace, expected)

    def test_source_errors_and_printer(self):
        for expression in (N(-1), U("+1", N(1)), O("/", N(1), N(1)), Fst(N(1)), A(N(1), N(2))):
            with self.subTest(expression=expression), self.assertRaises(EvaluationError):
                evaluate(expression)
        self.assertEqual(format_source(O("+", N(1), N(2))), "(1 + 2)")


if __name__ == "__main__":
    unittest.main()
