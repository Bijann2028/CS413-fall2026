"""Closed Church combinators, expanded exclusively into Var/Lam/App nodes.

Representations and Z follow Assign06.md. Predecessor uses the independently
explained state-pair construction in DESIGN.md; no builder executes a program.
"""

from .terms import Var as V, Lam as L, apps as A, lams


def identity():
    return L("w", V("w"))


def boolean(value: bool):
    return lams("t f", V("t" if value else "f"))


def numeral(value: int):
    if type(value) is not int or value < 0:
        raise ValueError(f"expected a natural literal, got {value!r}")
    body = V("z")
    for _ in range(value):
        body = A(V("s"), body)
    return lams("s z", body)


def pair():
    return lams("a b p", A(V("p"), V("a"), V("b")))


def first():
    return L("p", A(V("p"), boolean(True)))


def second():
    return L("p", A(V("p"), boolean(False)))


def successor():
    return lams("n s z", A(V("s"), A(V("n"), V("s"), V("z"))))


def predecessor():
    # The iterator moves (previous, current) to (current, current + 1).
    current = A(second(), V("p"))
    step = L("p", A(pair(), current, A(successor(), current)))
    initial = A(pair(), numeral(0), numeral(0))
    return L("n", A(first(), A(V("n"), step, initial)))


def is_zero():
    return L("n", A(V("n"), L("ignored", boolean(False)), boolean(True)))


def addition():
    return lams("m n s z", A(V("m"), V("s"), A(V("n"), V("s"), V("z"))))


def subtraction():
    return lams("m n", A(V("n"), predecessor(), V("m")))


def multiplication():
    return lams("m n s", A(V("m"), A(V("n"), V("s"))))


def negation():
    return L("b", A(V("b"), boolean(False), boolean(True)))


def conjunction():
    """Boolean value combinator; source short-circuiting is compiled as thunks."""
    return lams("p q", A(V("p"), V("q"), boolean(False)))


def disjunction():
    return lams("p q", A(V("p"), boolean(True), V("q")))


def less_equal():
    return lams("m n", A(is_zero(), A(subtraction(), V("m"), V("n"))))


def greater_equal():
    return lams("m n", A(less_equal(), V("n"), V("m")))


def less_than():
    return lams("m n", A(negation(), A(less_equal(), V("n"), V("m"))))


def greater_than():
    return lams("m n", A(negation(), A(less_equal(), V("m"), V("n"))))


def equal():
    return lams("m n", A(conjunction(),
                         A(less_equal(), V("m"), V("n")),
                         A(less_equal(), V("n"), V("m"))))


def not_equal():
    return lams("m n", A(negation(), A(equal(), V("m"), V("n"))))


def fixed_point():
    # Z delays recursive self-application behind a one-argument lambda.
    half = L("x", A(V("g"), L("v", A(V("x"), V("x"), V("v")))))
    return L("g", A(half, half))


BINARY_BUILDERS = {
    "+": addition, "-": subtraction, "*": multiplication,
    "<": less_than, "<=": less_equal, ">": greater_than, ">=": greater_equal,
    "==": equal, "!=": not_equal,
}

LIBRARY_BUILDERS = {
    "identity": identity, "true": lambda: boolean(True),
    "false": lambda: boolean(False), "zero": lambda: numeral(0),
    "pair": pair, "first": first, "second": second,
    "successor": successor, "predecessor": predecessor, "is_zero": is_zero,
    "addition": addition, "subtraction": subtraction, "multiplication": multiplication,
    "negation": negation, "conjunction": conjunction, "disjunction": disjunction,
    "less_equal": less_equal, "greater_equal": greater_equal,
    "less_than": less_than, "greater_than": greater_than,
    "equal": equal, "not_equal": not_equal, "Z": fixed_point,
}
