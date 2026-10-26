"""One iterative, weak, left-to-right call-by-value evaluation machine.

Source and target share variable/lambda/application traversal and application
frames. Only source-only frames can reach Python data operations. Target beta
steps use capture-avoiding substitution on pure target syntax exclusively.
"""

from dataclasses import dataclass
import operator

from .source import (
    D0E000, D0Eint, D0Ebtf, D0Evar, D0Elam, D0Eapp, D0Efix, D0Eop1,
    D0Eop2, D0Eif0, D0Elet, D0Epair, D0Epfst, D0Epsnd, d0exp_fvset,
)
from .source_ops import substitute_source
from .terms import Var, Lam, App, free_variables, substitute, walk


class EvaluationError(ValueError):
    """A term is open, stuck, or uses an unsupported source operation."""


@dataclass(frozen=True)
class EvaluationResult:
    status: str
    value: object | None
    steps: int

    @property
    def completed(self):
        return self.status == "completed"


def _is_value(expression):
    if isinstance(expression, (Lam, D0Elam, D0Efix, D0Eint, D0Ebtf)):
        return True
    if isinstance(expression, D0Epair):
        return _is_value(expression.arg1) and _is_value(expression.arg2)
    return False


def _boolean(value):
    if not isinstance(value, D0Ebtf):
        raise EvaluationError("source boolean required")
    return value.arg1


def _source_binary(name, left, right):
    """Source primitives only. Target execution never enters this function."""
    if name in ("and", "or"):
        a, b = _boolean(left), _boolean(right)
        return D0Ebtf(a and b if name == "and" else a or b)
    if not isinstance(left, D0Eint) or not isinstance(right, D0Eint):
        raise EvaluationError(f"natural operands required for {name!r}")
    a, b = left.arg1, right.arg1
    match name:
        case "+":
            return D0Eint(a + b)
        case "-":
            return D0Eint(max(a - b, 0))
        case "*":
            return D0Eint(a * b)
        case "<" | "<=" | ">" | ">=" | "==" | "!=":
            comparison = {"<": operator.lt, "<=": operator.le, ">": operator.gt,
                          ">=": operator.ge, "==": operator.eq, "!=": operator.ne}[name]
            return D0Ebtf(comparison(a, b))
        case _:
            raise EvaluationError(f"unsupported source binary operator: {name!r}")


def evaluate(expression, max_steps: int | None = None, *, on_beta=None) -> EvaluationResult:
    """Run either AST through the same evaluation loop.

    Execution requires a closed expression. Target budget defaults to 10,000
    beta-value steps; source evaluation is unbounded unless a budget is given.
    An optional callback receives (function, argument) at each actual beta step.
    Administrative frame transitions and source primitives are not beta steps.
    """
    target = isinstance(expression, (Var, Lam, App))
    if max_steps is not None and (type(max_steps) is not int or max_steps < 0):
        raise ValueError("max_steps must be a nonnegative integer")
    if target:
        # Fail before execution if any source node has been embedded in a target.
        for _ in walk(expression):
            pass
        free = free_variables(expression)
        if max_steps is None:
            max_steps = 10_000
    elif isinstance(expression, D0E000):
        free = d0exp_fvset(expression)
    else:
        raise TypeError("evaluate expects a source AST or a pure target term")
    if free:
        raise EvaluationError(f"execution requires a closed term; free names: {sorted(free)}")

    control, stack, steps = expression, [], 0
    while True:
        if _is_value(control):
            if isinstance(control, D0Eint) and control.arg1 < 0:
                raise EvaluationError(f"negative source literal: {control.arg1}")
            if not stack:
                return EvaluationResult("completed", control, steps)
            frame = stack.pop()
            match frame:
                case ("function", argument):
                    stack.append(("argument", control))
                    control = argument
                case ("argument", function):
                    argument = control
                    if not isinstance(function, (Lam, D0Elam, D0Efix)):
                        raise EvaluationError("application requires a function")
                    if max_steps is not None and steps == max_steps:
                        return EvaluationResult("exhausted", None, steps)
                    if on_beta is not None:
                        on_beta(function, argument)
                    steps += 1
                    if isinstance(function, Lam):
                        control = substitute(function.body, function.name, argument)
                    elif isinstance(function, D0Elam):
                        control = substitute_source(function.arg2, function.arg1, argument)
                    else:
                        body = function.arg3
                        if function.arg1 != function.arg2:
                            body = substitute_source(body, function.arg1, function)
                        control = substitute_source(body, function.arg2, argument)
                case ("let", name, body):
                    control = substitute_source(body, name, control)
                case ("if", when_true, when_false):
                    control = when_true if _boolean(control) else when_false
                case ("pair_left", right):
                    stack.append(("pair_right", control))
                    control = right
                case ("pair_right", left):
                    control = D0Epair(left, control)
                case ("projection", side):
                    if not isinstance(control, D0Epair):
                        raise EvaluationError("projection requires a pair")
                    control = control.arg1 if side == "first" else control.arg2
                case ("unary", "not"):
                    control = D0Ebtf(not _boolean(control))
                case ("binary_left", name, right):
                    if name == "and" and not _boolean(control):
                        control = D0Ebtf(False)
                    elif name == "or" and _boolean(control):
                        control = D0Ebtf(True)
                    else:
                        stack.append(("binary_right", name, control))
                        control = right
                case ("binary_right", name, left):
                    control = _source_binary(name, left, control)
                case _:
                    raise AssertionError(f"unknown continuation: {frame[0]}")
            continue

        # Both representations use the same application traversal and frames.
        if isinstance(control, App):
            stack.append(("function", control.arg))
            control = control.fn
        elif isinstance(control, D0Eapp):
            stack.append(("function", control.arg2))
            control = control.arg1
        elif isinstance(control, (Var, D0Evar)):
            raise EvaluationError("unbound variable reached during execution")
        elif isinstance(control, D0Elet):
            stack.append(("let", control.arg1, control.arg3))
            control = control.arg2
        elif isinstance(control, D0Eif0):
            stack.append(("if", control.arg2, control.arg3))
            control = control.arg1
        elif isinstance(control, D0Epair):
            stack.append(("pair_left", control.arg2))
            control = control.arg1
        elif isinstance(control, (D0Epfst, D0Epsnd)):
            side = "first" if isinstance(control, D0Epfst) else "second"
            stack.append(("projection", side))
            control = control.arg1
        elif isinstance(control, D0Eop1):
            if control.name != "not":
                raise EvaluationError(f"unsupported source unary operator: {control.name!r}")
            stack.append(("unary", control.name))
            control = control.arg1
        elif isinstance(control, D0Eop2):
            if control.name not in ("+", "-", "*", "<", "<=", ">", ">=", "==", "!=", "and", "or"):
                raise EvaluationError(f"unsupported source binary operator: {control.name!r}")
            stack.append(("binary_left", control.name, control.arg2))
            control = control.arg1
        else:
            raise EvaluationError(f"unsupported expression: {type(control).__name__}")


def source_data(value):
    """Read a completed source data value for comparison; never compiles it."""
    match value:
        case D0Eint(n) | D0Ebtf(n):
            return n
        case D0Epair(left, right):
            return source_data(left), source_data(right)
        case _:
            raise EvaluationError("expected a natural, boolean, or finite source pair")
