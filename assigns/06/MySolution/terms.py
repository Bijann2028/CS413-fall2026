"""Immutable pure target terms and non-evaluating scope operations."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Var:
    name: str


@dataclass(frozen=True, slots=True)
class Lam:
    name: str
    body: "Term"


@dataclass(frozen=True, slots=True)
class App:
    fn: "Term"
    arg: "Term"


type Term = Var | Lam | App


def apps(fn: Term, *arguments: Term) -> Term:
    """Left-associated application; only constructs syntax."""
    for argument in arguments:
        fn = App(fn, argument)
    return fn


def lams(names: str, body: Term) -> Term:
    """Builder shorthand; each emitted Lam still has exactly one binder."""
    for name in reversed(names.split()):
        body = Lam(name, body)
    return body


def walk(term: Term):
    """Iterative traversal also validates that every node is pure target syntax."""
    pending = [term]
    while pending:
        node = pending.pop()
        if type(node) not in (Var, Lam, App):
            raise TypeError(f"not a pure target node: {type(node).__name__}")
        yield node
        if isinstance(node, Lam):
            pending.append(node.body)
        elif isinstance(node, App):
            pending.extend((node.arg, node.fn))


def all_names(term: Term) -> set[str]:
    return {node.name for node in walk(term) if isinstance(node, (Var, Lam))}


def free_variables(term: Term) -> frozenset[str]:
    """Compute free names without relying on Python's recursion depth."""
    free = set()
    pending = [(term, frozenset())]
    while pending:
        node, bound = pending.pop()
        match node:
            case Var(name):
                if name not in bound:
                    free.add(name)
            case Lam(name, body):
                pending.append((body, bound | {name}))
            case App(fn, arg):
                pending.extend(((arg, bound), (fn, bound)))
            case _:
                raise TypeError(f"not a target term: {type(node).__name__}")
    return frozenset(free)


class FreshNames:
    """Deterministic per-operation supply; no global counters or reserved names."""

    def __init__(self, reserved=()):
        self.reserved = set(reserved)

    def fresh(self, base: str = "u") -> str:
        index = 1
        while f"{base}_{index}" in self.reserved:
            index += 1
        name = f"{base}_{index}"
        self.reserved.add(name)
        return name


def substitute(term: Term, variable: str, replacement: Term) -> Term:
    """Single capture-avoiding substitution, with iterative rebuilding.

    Renaming is scoped: a lambda shadowing a renamed binder replaces the
    current renaming entry. Replacement terms are inserted without traversal.
    """
    replacement_free = free_variables(replacement)
    supply = FreshNames(all_names(term) | all_names(replacement) | {variable})
    tasks = [("visit", term, {}, True)]
    results = []
    while tasks:
        task = tasks.pop()
        if task[0] == "lam":
            results.append(Lam(task[1], results.pop()))
            continue
        if task[0] == "app":
            arg, fn = results.pop(), results.pop()
            results.append(App(fn, arg))
            continue
        _, node, renaming, active = task
        match node:
            case Var(name):
                if active and name == variable:
                    results.append(replacement)
                else:
                    results.append(Var(renaming.get(name, name)))
            case Lam(name, body):
                inside_active = active and name != variable
                fresh = name
                if inside_active and name in replacement_free:
                    fresh = supply.fresh(name)
                inside_names = {**renaming, name: fresh}
                tasks.extend((("lam", fresh),
                              ("visit", body, inside_names, inside_active)))
            case App(fn, arg):
                tasks.extend((("app",), ("visit", arg, renaming, active),
                              ("visit", fn, renaming, active)))
            case _:
                raise TypeError(f"not a target term: {type(node).__name__}")
    return results[0]


def format_term(term: Term) -> str:
    pieces = []
    pending = [term]
    while pending:
        node = pending.pop()
        match node:
            case str():
                pieces.append(node)
            case Var(name):
                pieces.append(name)
            case Lam(name, body):
                pieces.append(f"(lam {name}. ")
                pending.extend((")", body))
            case App(fn, arg):
                pieces.append("(")
                pending.extend((")", arg, " ", fn))
            case _:
                raise TypeError(f"not a target term: {type(node).__name__}")
    return "".join(pieces)


def alpha_equivalent(left: Term, right: Term) -> bool:
    """Compare binder positions, not their spelling; preserve free-name identity."""
    pending = [(left, right, (), ())]
    while pending:
        a, b, left_scope, right_scope = pending.pop()
        if type(a) is not type(b):
            return False
        match a, b:
            case Var(x), Var(y):
                left_index = left_scope.index(x) if x in left_scope else None
                right_index = right_scope.index(y) if y in right_scope else None
                if left_index != right_index:
                    return False
                if left_index is None and x != y:
                    return False
            case Lam(x, body_a), Lam(y, body_b):
                pending.append((body_a, body_b, (x,) + left_scope, (y,) + right_scope))
            case App(fn_a, arg_a), App(fn_b, arg_b):
                pending.extend(((fn_a, fn_b, left_scope, right_scope),
                                (arg_a, arg_b, left_scope, right_scope)))
            case _:
                raise TypeError("alpha-equivalence expects pure target terms")
    return True
