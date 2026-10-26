"""The fourteen required examples, as source ASTs with independent answers."""

from dataclasses import dataclass

from .source import (
    D0Eint as N, D0Ebtf as B, D0Evar as V, D0Elam as L, D0Eapp as A,
    D0Efix as F, D0Eop2 as O, D0Eif0 as If, D0Elet as Let,
    D0Epair as Pair, D0Epfst as Fst, D0Epsnd as Snd,
)


@dataclass(frozen=True)
class Example:
    name: str
    expression: object
    kind: str
    expected: object
    exhausts: bool = False
    execution_budget: int = 20_000
    observation_budget: int = 10_000


def loop():
    return A(F("loop", "x", A(V("loop"), V("x"))), N(0))


def factorial(n=4):
    body = If(O("==", V("n"), N(0)), N(1),
              O("*", V("n"), A(V("fact"), O("-", V("n"), N(1)))))
    return A(F("fact", "n", body), N(n))


def fibonacci(n=5):
    body = If(O("<=", V("n"), N(1)), V("n"),
              O("+", A(V("fib"), O("-", V("n"), N(1))),
                A(V("fib"), O("-", V("n"), N(2)))))
    return A(F("fib", "n", body), N(n))


def required_examples():
    return [
        Example("arithmetic", O("+", N(2), O("*", N(3), N(4))), "nat", 14),
        Example("truncated_subtraction", O("-", N(2), N(5)), "nat", 0),
        Example("comparison_conditional", If(O("<=", N(2), N(3)), N(7), N(9)), "nat", 7),
        Example("lexical_let", Let("x", N(3), A(L("y", O("+", V("x"), V("y"))), N(4))), "nat", 7),
        Example("first_projection", Fst(Pair(N(2), B(True))), "nat", 2),
        Example("second_projection", Snd(Pair(N(2), B(True))), "bool", True),
        Example("higher_order", A(L("f", A(V("f"), N(3))), L("x", O("+", V("x"), N(1)))), "nat", 4),
        Example("conjunction", O("and", B(True), B(False)), "bool", False),
        Example("disjunction", O("or", B(False), B(True)), "bool", True),
        Example("skipped_loop", If(B(True), N(1), loop()), "nat", 1),
        Example("strict_argument", A(L("x", N(0)), loop()), "nat", None, True, 200),
        Example("factorial", factorial(), "nat", 24),
        Example("fibonacci", fibonacci(), "nat", 5),
        Example("loop", loop(), "nat", None, True, 200),
    ]
