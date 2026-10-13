import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from copy import deepcopy
from unittest.mock import patch
import pytest
from lambda1_vp import d0exp_fvset, D0ExpVisitor, D0Evar, D0Eint
from MySolution import PrettyPrintVisitor, SubstitutionVisitor, d0exp_pretty, d0exp_substitute
from MySolution.TEST.cases import PRINT_CASES, SUB_CASES


@pytest.mark.parametrize("expression,expected", PRINT_CASES)
def test_exact_printing(expression, expected):
    before = deepcopy(expression)
    assert d0exp_pretty(expression) == expected
    assert expression == before


@pytest.mark.parametrize("label,expression,target,replacement,expected", SUB_CASES,
                         ids=[case[0] for case in SUB_CASES])
def test_substitution_scope_and_capture(label, expression, target, replacement, expected):
    assert d0exp_pretty(d0exp_substitute(expression, target, replacement)) == expected


@pytest.mark.parametrize("label,expression,target,replacement,expected", SUB_CASES,
                         ids=[case[0] for case in SUB_CASES])
def test_preservation_and_determinism(label, expression, target, replacement, expected):
    before_e, before_r = deepcopy(expression), deepcopy(replacement)
    first = d0exp_substitute(expression, target, replacement)
    assert first == d0exp_substitute(expression, target, replacement)
    assert expression == before_e
    assert replacement == before_r


@pytest.mark.parametrize("label,expression,target,replacement,expected", SUB_CASES,
                         ids=[case[0] for case in SUB_CASES])
def test_free_variable_property(label, expression, target, replacement, expected):
    original_fv = d0exp_fvset(expression)
    result = d0exp_substitute(expression, target, replacement)
    expected_fv = ((original_fv - {target}) | d0exp_fvset(replacement)
                   if target in original_fv else original_fv)
    assert d0exp_fvset(result) == expected_fv
    if target not in original_fv:
        assert result == expression


def test_no_evaluation():
    with patch("lambda1_vp.EvaluateVisitor", side_effect=AssertionError("evaluation forbidden")), \
         patch("lambda1_vp.d0exp_evaluate", side_effect=AssertionError("evaluation forbidden")):
        for expression, expected in PRINT_CASES:
            assert d0exp_pretty(expression) == expected
        for _, expression, target, replacement, expected in SUB_CASES:
            assert d0exp_pretty(d0exp_substitute(expression, target, replacement)) == expected


def test_direct_visitor_dispatch_and_replacement_identity():
    expression, replacement = D0Evar("x"), D0Eint(9)
    printer = PrettyPrintVisitor()
    substitute = SubstitutionVisitor(expression, "x", replacement)
    assert isinstance(printer, D0ExpVisitor)
    assert isinstance(substitute, D0ExpVisitor)
    assert expression.accept(printer) == "x"
    assert expression.accept(substitute) is replacement
