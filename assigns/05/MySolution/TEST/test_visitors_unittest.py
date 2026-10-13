import sys
from pathlib import Path

# Resolve imports from this file, independently of the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import unittest
from copy import deepcopy
from unittest.mock import patch
from lambda1_vp import d0exp_fvset, D0ExpVisitor, D0Evar, D0Eint
from MySolution import PrettyPrintVisitor, SubstitutionVisitor, d0exp_pretty, d0exp_substitute
from MySolution.TEST.cases import PRINT_CASES, SUB_CASES


class VisitorTests(unittest.TestCase):
    def test_exact_printing(self):
        for expression, expected in PRINT_CASES:
            with self.subTest(expected=expected):
                before = deepcopy(expression)
                self.assertEqual(d0exp_pretty(expression), expected)
                self.assertEqual(expression, before)

    def test_substitution_scope_and_capture(self):
        for label, expression, target, replacement, expected in SUB_CASES:
            with self.subTest(case=label):
                self.assertEqual(d0exp_pretty(d0exp_substitute(expression, target, replacement)), expected)

    def test_preservation_and_determinism(self):
        for label, expression, target, replacement, _ in SUB_CASES:
            with self.subTest(case=label):
                before_e, before_r = deepcopy(expression), deepcopy(replacement)
                first = d0exp_substitute(expression, target, replacement)
                second = d0exp_substitute(expression, target, replacement)
                self.assertEqual(first, second)
                self.assertEqual(expression, before_e)
                self.assertEqual(replacement, before_r)

    def test_free_variable_property(self):
        for label, expression, target, replacement, _ in SUB_CASES:
            with self.subTest(case=label):
                original_fv = d0exp_fvset(expression)
                result = d0exp_substitute(expression, target, replacement)
                expected = ((original_fv - {target}) | d0exp_fvset(replacement)
                            if target in original_fv else original_fv)
                self.assertEqual(d0exp_fvset(result), expected)
                if target not in original_fv:
                    self.assertEqual(result, expression)

    def test_no_evaluation(self):
        with patch("lambda1_vp.EvaluateVisitor", side_effect=AssertionError("evaluation forbidden")), \
             patch("lambda1_vp.d0exp_evaluate", side_effect=AssertionError("evaluation forbidden")):
            for expression, expected in PRINT_CASES:
                self.assertEqual(d0exp_pretty(expression), expected)
            for _, expression, target, replacement, expected in SUB_CASES:
                self.assertEqual(d0exp_pretty(d0exp_substitute(expression, target, replacement)), expected)

    def test_direct_visitor_dispatch_and_replacement_identity(self):
        expression, replacement = D0Evar("x"), D0Eint(9)
        printer = PrettyPrintVisitor()
        substitute = SubstitutionVisitor(expression, "x", replacement)
        self.assertIsInstance(printer, D0ExpVisitor)
        self.assertIsInstance(substitute, D0ExpVisitor)
        self.assertEqual(expression.accept(printer), "x")
        self.assertIs(expression.accept(substitute), replacement)


if __name__ == "__main__":
    unittest.main()
