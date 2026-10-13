"""Visitor traversals shared by substitution and scoped alpha-renaming."""
from lambda1_vp import (
    D0ExpVisitor, FreeVariableVisitor, d0exp, D0Eop1, D0Eop2, D0Eapp,
    D0Eif0, D0Epair, D0Epfst, D0Epsnd, D0Evar, D0Elam, D0Efix, D0Elet,
)


class AllNamesVisitor(FreeVariableVisitor):
    """Collect bound names as well as free names, including unused binders."""
    def visit_lam(self, e):
        return frozenset({e.arg1}) | e.arg2.accept(self)

    def visit_fix(self, e):
        return frozenset({e.arg1, e.arg2}) | e.arg3.accept(self)

    def visit_let(self, e):
        return frozenset({e.arg1}) | e.arg2.accept(self) | e.arg3.accept(self)


class FreshNames:
    def __init__(self, reserved):
        self.reserved = set(reserved)

    def fresh(self, base):
        counter = 1
        while f"{base}_{counter}" in self.reserved:
            counter += 1
        name = f"{base}_{counter}"
        self.reserved.add(name)
        return name


class TransformVisitor(D0ExpVisitor[d0exp]):
    """Rebuild nonbinding forms; subclasses supply variable and binder rules."""
    def visit_int(self, e):
        return e

    def visit_btf(self, e):
        return e

    def visit_op1(self, e):
        return D0Eop1(e.name, e.arg1.accept(self))

    def visit_op2(self, e):
        return D0Eop2(e.name, e.arg1.accept(self), e.arg2.accept(self))

    def visit_app(self, e):
        return D0Eapp(e.arg1.accept(self), e.arg2.accept(self))

    def visit_if0(self, e):
        return D0Eif0(e.arg1.accept(self), e.arg2.accept(self), e.arg3.accept(self))

    def visit_pair(self, e):
        return D0Epair(e.arg1.accept(self), e.arg2.accept(self))

    def visit_pfst(self, e):
        return D0Epfst(e.arg1.accept(self))

    def visit_psnd(self, e):
        return D0Epsnd(e.arg1.accept(self))


class RenameVisitor(TransformVisitor):
    """Rename occurrences of an outer binder, stopping at inner shadowing."""
    def __init__(self, old, new):
        self.old, self.new = old, new

    def visit_var(self, e):
        return D0Evar(self.new) if e.arg1 == self.old else e

    def visit_lam(self, e):
        body = e.arg2 if e.arg1 == self.old else e.arg2.accept(self)
        return D0Elam(e.arg1, body)

    def visit_fix(self, e):
        body = e.arg3 if self.old in (e.arg1, e.arg2) else e.arg3.accept(self)
        return D0Efix(e.arg1, e.arg2, body)

    def visit_let(self, e):
        init = e.arg2.accept(self)
        body = e.arg3 if e.arg1 == self.old else e.arg3.accept(self)
        return D0Elet(e.arg1, init, body)
