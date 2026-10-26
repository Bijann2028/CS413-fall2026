import copy
import unittest

from MySolution.terms import (
    Var as V, Lam as L, App as A, apps, format_term, free_variables,
    all_names, substitute, alpha_equivalent, walk,
)
from MySolution.evaluator import evaluate, EvaluationError


class TargetOperationsTests(unittest.TestCase):
    def test_exact_printer(self):
        cases = [(V("x"), "x"), (L("x", V("x")), "(lam x. x)"),
                 (A(V("f"), V("x")), "(f x)"),
                 (A(L("x", V("x")), A(V("f"), V("y"))), "((lam x. x) (f y))")]
        for term, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(format_term(term), expected)

    def test_free_and_bound_names(self):
        term = L("x", A(V("x"), L("y", A(V("x"), V("z")))))
        self.assertEqual(free_variables(term), {"z"})
        self.assertEqual(all_names(term), {"x", "y", "z"})

    def test_capture_avoidance_independent_of_execution(self):
        term, replacement = L("y", V("x")), V("y")
        snapshot = copy.deepcopy((term, replacement))
        result = substitute(term, "x", replacement)
        self.assertTrue(alpha_equivalent(result, L("fresh", V("y"))))
        self.assertEqual(free_variables(result), {"y"})
        self.assertEqual((term, replacement), snapshot)

    def test_substitution_shadowing_and_nested_shadowing(self):
        cases = [
            (L("x", V("x")), L("x", V("x"))),
            (L("y", A(V("x"), L("y", V("y")))),
             L("a", A(V("y"), L("b", V("b"))))),
            (L("y", A(V("y"), L("y", V("x")))),
             L("a", A(V("a"), L("b", V("y"))))),
            (L("y", L("x", A(V("y"), V("x")))),
             L("a", L("x", A(V("a"), V("x"))))),
        ]
        for term, expected in cases:
            with self.subTest(term=term):
                self.assertTrue(alpha_equivalent(substitute(term, "x", V("y")), expected))

    def test_replacement_is_not_recursively_substituted(self):
        replacement = A(V("x"), V("y"))
        result = substitute(A(V("x"), V("x")), "x", replacement)
        self.assertEqual(result, A(replacement, replacement))

    def test_freshness_includes_existing_bound_names(self):
        term = L("y", L("y_1", A(V("x"), V("y"))))
        result = substitute(term, "x", V("y"))
        self.assertNotIn(result.name, {"y", "y_1"})
        self.assertEqual(free_variables(result), {"y"})
        self.assertEqual(result, substitute(term, "x", V("y")))

    def test_free_variable_substitution_law(self):
        terms = [V("x"), V("z"), L("x", V("x")), L("y", V("x")),
                 A(V("x"), L("z", A(V("y"), V("z"))))]
        replacements = [V("x"), V("y"), A(V("y"), V("z")), L("y", V("y"))]
        for term in terms:
            for replacement in replacements:
                with self.subTest(term=term, replacement=replacement):
                    expected = free_variables(term) - {"x"}
                    if "x" in free_variables(term):
                        expected |= free_variables(replacement)
                    self.assertEqual(free_variables(substitute(term, "x", replacement)), expected)

    def test_alpha_equivalence_respects_binding_positions_and_free_names(self):
        self.assertTrue(alpha_equivalent(L("x", L("x", V("x"))), L("a", L("b", V("b")))))
        self.assertFalse(alpha_equivalent(L("x", L("y", V("x"))), L("a", L("b", V("b")))))
        self.assertFalse(alpha_equivalent(V("x"), V("y")))
        self.assertFalse(alpha_equivalent(L("x", V("x")), L("x", V("y"))))

    def test_deep_pure_operations_do_not_need_python_recursion(self):
        term = V("x")
        for _ in range(1200):
            term = A(V("f"), term)
        result = substitute(term, "x", V("y"))
        self.assertEqual(free_variables(result), {"f", "y"})
        self.assertEqual(len(list(walk(result))), 2401)
        self.assertTrue(format_term(result).endswith("y" + ")" * 1200))


class TargetEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.identity = L("x", V("x"))

    def test_budget_boundaries(self):
        for term, budget, status, count in [
            (self.identity, 0, "completed", 0),
            (A(self.identity, self.identity), 0, "exhausted", 0),
            (A(self.identity, self.identity), 1, "completed", 1),
            (A(self.identity, A(self.identity, self.identity)), 1, "exhausted", 1),
            (A(self.identity, A(self.identity, self.identity)), 2, "completed", 2),
        ]:
            with self.subTest(budget=budget, term=term):
                result = evaluate(term, budget)
                self.assertEqual((result.status, result.steps), (status, count))
                if result.completed:
                    self.assertEqual(result.value, self.identity)
                else:
                    self.assertIsNone(result.value)

    def test_left_to_right_function_then_argument_then_application(self):
        left = A(L("left", V("left")), L("outer", V("outer")))
        right = A(L("right", V("right")), self.identity)
        trace = []
        result = evaluate(A(left, right), 3, on_beta=lambda fn, arg: trace.append(fn.name))
        self.assertEqual(trace, ["left", "right", "outer"])
        self.assertEqual(result.steps, 3)
        self.assertEqual(result.value, self.identity)

    def test_weak_evaluation_and_no_eta_reduction(self):
        term = L("f", L("x", A(V("f"), V("x"))))
        redex_body = L("x", A(self.identity, V("x")))
        for value in (term, redex_body):
            with self.subTest(value=value):
                result = evaluate(value, 0)
                self.assertEqual(result.value, value)
                self.assertEqual(result.steps, 0)

    def test_omega_exhaustion_and_determinism(self):
        half = L("x", A(V("x"), V("x")))
        omega = A(half, half)
        snapshot = copy.deepcopy(omega)
        first, second = evaluate(omega, 100), evaluate(omega, 100)
        self.assertEqual(first, second)
        self.assertEqual((first.status, first.steps), ("exhausted", 100))
        self.assertEqual(omega, snapshot)

    def test_diverging_function_is_evaluated_before_argument(self):
        half = L("x", A(V("x"), V("x")))
        trace = []
        argument = A(L("argument", V("argument")), self.identity)
        result = evaluate(A(A(half, half), argument), 12,
                          on_beta=lambda fn, arg: trace.append(fn.name))
        self.assertEqual(result.status, "exhausted")
        self.assertNotIn("argument", trace)

    def test_reject_bad_budgets_open_and_mixed_terms(self):
        for budget in (-1, True, 1.5):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                evaluate(self.identity, budget)
        with self.assertRaisesRegex(EvaluationError, "closed"):
            evaluate(L("x", V("free")), 0)
        from MySolution.source import D0Eint
        with self.assertRaises(TypeError):
            evaluate(A(self.identity, D0Eint(1)), 10)


if __name__ == "__main__":
    unittest.main()
