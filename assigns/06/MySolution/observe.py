"""Bounded pure-target observations, followed only by structural inspection."""

from dataclasses import dataclass

from . import church
from .evaluator import evaluate, EvaluationError
from .terms import Var, Lam, App, Term, apps, lams, alpha_equivalent, free_variables


@dataclass(frozen=True)
class PairKind:
    left: "Kind"
    right: "Kind"


type Kind = str | PairKind


@dataclass(frozen=True)
class Observation:
    status: str
    value: object | None
    steps: int
    message: str = ""


class _Malformed(ValueError):
    pass


class _Exhausted(Exception):
    pass


class _Budget:
    """One aggregate observation budget, shared by all nested projections."""

    def __init__(self, limit):
        if type(limit) is not int or limit < 0:
            raise ValueError("observation budget must be a nonnegative integer")
        self.limit, self.steps = limit, 0

    def run(self, term):
        try:
            result = evaluate(term, self.limit - self.steps)
        except EvaluationError as error:
            raise _Malformed(str(error)) from error
        self.steps += result.steps
        if not result.completed:
            raise _Exhausted
        return result.value


def _count_spine(value):
    count = 0
    while True:
        if not isinstance(value, Lam) or not isinstance(value.body, Lam):
            raise _Malformed("natural observation did not produce a two-binder spine")
        constructor, zero, body = value.name, value.body.name, value.body.body
        if isinstance(body, Var) and body.name == zero:
            return count
        if (constructor != zero and isinstance(body, App)
                and isinstance(body.fn, Var) and body.fn.name == constructor
                and not (free_variables(body.arg) & {constructor, zero})):
            count += 1
            value = body.arg
        else:
            raise _Malformed("malformed natural observation spine")


def _observe(term: Term, kind: Kind, budget: _Budget):
    # A lambda with hidden redexes is a completed value, not a normal form.
    value = budget.run(term)
    if kind == "nat":
        step = lams("tail c z", App(Var("c"), Var("tail")))
        base = lams("c z", Var("z"))
        spine = budget.run(apps(value, step, base))
        return _count_spine(spine)
    if kind == "bool":
        true_marker = church.identity()
        false_marker = lams("marker unused", Var("marker"))
        marker = budget.run(apps(value, true_marker, false_marker))
        if alpha_equivalent(marker, true_marker):
            return True
        if alpha_equivalent(marker, false_marker):
            return False
        raise _Malformed("boolean observation did not select a marker")
    if isinstance(kind, PairKind):
        left = budget.run(App(church.first(), value))
        left_data = _observe(left, kind.left, budget)
        right = budget.run(App(church.second(), value))
        right_data = _observe(right, kind.right, budget)
        return left_data, right_data
    raise ValueError(f"expected 'nat', 'bool', or PairKind, got {kind!r}")


def observe(term: Term, kind: Kind, max_steps: int = 10_000) -> Observation:
    """Do not infer a kind: Church zero and false are alpha-equivalent.

    All evaluation uses the shared engine. Python counts the final inert
    spine or recognizes a final marker; it never executes Church arithmetic.
    """
    budget = _Budget(max_steps)
    try:
        data = _observe(term, kind, budget)
    except _Exhausted:
        return Observation("exhausted", None, budget.steps, "observation budget exhausted")
    except _Malformed as error:
        return Observation("malformed", None, budget.steps, str(error))
    return Observation("completed", data, budget.steps)
