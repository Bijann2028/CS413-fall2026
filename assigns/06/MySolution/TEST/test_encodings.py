import unittest

from MySolution import church
from MySolution.terms import (
    Var as V, Lam as L, App as A, apps, lams, free_variables, alpha_equivalent, walk,
)
from MySolution.evaluator import evaluate
from MySolution.observe import observe, PairKind


class EncodingTests(unittest.TestCase):
    def check(self, term, kind, expected):
        execution = evaluate(term, 20_000)
        self.assertTrue(execution.completed)
        result = observe(execution.value, kind, 20_000)
        self.assertEqual(result.status, "completed", result.message)
        self.assertIs(type(result.value), type(expected))
        self.assertEqual(result.value, expected)

    def test_every_library_combinator_is_closed_and_pure(self):
        for name, builder in church.LIBRARY_BUILDERS.items():
            with self.subTest(name=name):
                term = builder()
                self.assertFalse(free_variables(term))
                self.assertTrue(list(walk(term)))

    def test_specified_representations(self):
        self.assertTrue(alpha_equivalent(church.boolean(True), lams("t f", V("t"))))
        self.assertTrue(alpha_equivalent(church.boolean(False), lams("t f", V("f"))))
        self.assertTrue(alpha_equivalent(church.numeral(2), lams("s z", A(V("s"), A(V("s"), V("z"))))))
        self.assertTrue(alpha_equivalent(church.pair(), lams("a b p", apps(V("p"), V("a"), V("b")))))

    def test_numerals_successor_predecessor_and_zero(self):
        for n in range(5):
            with self.subTest(n=n):
                self.check(church.numeral(n), "nat", n)
                self.check(A(church.successor(), church.numeral(n)), "nat", n + 1)
                self.check(A(church.predecessor(), church.numeral(n)), "nat", max(n - 1, 0))
                self.check(A(church.is_zero(), church.numeral(n)), "bool", n == 0)

    def test_all_natural_operators_on_small_grid(self):
        operations = {
            "+": lambda a, b: a + b, "-": lambda a, b: max(a - b, 0), "*": lambda a, b: a * b,
            "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
        }
        for op, expected_fn in operations.items():
            for a in range(4):
                for b in range(4):
                    with self.subTest(op=op, a=a, b=b):
                        expected = expected_fn(a, b)
                        kind = "bool" if type(expected) is bool else "nat"
                        term = apps(church.BINARY_BUILDERS[op](), church.numeral(a), church.numeral(b))
                        self.check(term, kind, expected)

    def test_boolean_truth_tables(self):
        for a in (False, True):
            with self.subTest(not_operand=a):
                self.check(A(church.negation(), church.boolean(a)), "bool", not a)
            for b in (False, True):
                with self.subTest(a=a, b=b):
                    self.check(apps(church.conjunction(), church.boolean(a), church.boolean(b)), "bool", a and b)
                    self.check(apps(church.disjunction(), church.boolean(a), church.boolean(b)), "bool", a or b)

    def test_pair_projections(self):
        pair = apps(church.pair(), church.numeral(3), church.boolean(True))
        self.check(A(church.first(), pair), "nat", 3)
        self.check(A(church.second(), pair), "bool", True)

    def test_call_by_value_fixed_point_returns_a_function(self):
        term = A(church.fixed_point(), lams("recursive x", V("x")))
        function = evaluate(term, 3)
        self.assertTrue(function.completed)
        self.assertIsInstance(function.value, L)
        self.check(A(function.value, church.numeral(3)), "nat", 3)


class ObservationTests(unittest.TestCase):
    def test_zero_needs_expected_kind(self):
        zero = church.numeral(0)
        self.assertTrue(alpha_equivalent(zero, church.boolean(False)))
        self.assertEqual(observe(zero, "nat").value, 0)
        self.assertIs(observe(zero, "bool").value, False)

    def test_alpha_renamed_and_computed_values(self):
        two = lams("increment start", A(V("increment"), A(V("increment"), V("start"))))
        self.assertEqual(observe(two, "nat").value, 2)
        true = lams("yes no", V("yes"))
        self.assertIs(observe(true, "bool").value, True)
        computed = evaluate(apps(church.addition(), church.numeral(2), church.numeral(3)), 10).value
        # Weak evaluation leaves a computed numeral's work beneath its lambdas.
        self.assertFalse(alpha_equivalent(computed, church.numeral(5)))
        self.assertEqual(observe(computed, "nat").value, 5)
        computed_bool = evaluate(A(church.negation(), church.boolean(False)), 20).value
        self.assertIs(observe(computed_bool, "bool").value, True)

    def test_separate_observation_budget_boundary(self):
        value = church.numeral(0)
        self.assertEqual(evaluate(value, 0).status, "completed")
        for limit, status, steps in [(0, "exhausted", 0), (1, "exhausted", 1), (2, "completed", 2)]:
            with self.subTest(limit=limit):
                result = observe(value, "nat", limit)
                self.assertEqual((result.status, result.steps), (status, steps))

    def test_malformed_outputs_are_not_successful_decodes(self):
        invalid = lams("a b", V("a"))
        self.assertEqual(observe(invalid, "nat").status, "malformed")
        invalid_bool = lams("a b extra ignored", V("ignored"))
        self.assertEqual(observe(invalid_bool, "bool").status, "malformed")
        self.assertEqual(observe(V("free"), "nat").status, "malformed")

    def test_observer_exhaustion_from_divergent_context(self):
        half = L("x", A(V("x"), V("x")))
        bad_numeral = lams("s z", A(half, half))
        result = observe(bad_numeral, "nat", 30)
        self.assertEqual((result.status, result.steps), ("exhausted", 30))

    def test_nested_pairs_and_aggregate_budget(self):
        pair = apps(church.pair(),
                    apps(church.pair(), church.numeral(2), church.boolean(True)), church.numeral(3))
        value = evaluate(pair, 20).value
        kind = PairKind(PairKind("nat", "bool"), "nat")
        result = observe(value, kind, 100)
        self.assertEqual((result.status, result.value), ("completed", ((2, True), 3)))
        self.assertGreater(result.steps, 0)
        exact = observe(value, kind, result.steps)
        self.assertEqual((exact.status, exact.value), ("completed", ((2, True), 3)))
        short = observe(value, kind, result.steps - 1)
        self.assertEqual(short.status, "exhausted")
        self.assertEqual(short.steps, result.steps - 1)

    def test_invalid_kind_and_budget_are_caller_errors(self):
        with self.assertRaises(ValueError):
            observe(church.numeral(0), "guess")
        for budget in (-1, True, 0.5):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                observe(church.numeral(0), "nat", budget)


if __name__ == "__main__":
    unittest.main()
