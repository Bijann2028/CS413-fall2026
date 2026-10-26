"""Source scope operations adapted from Bijan's Assignment 5 visitors.

Attribution: assigns/05/MySolution/{name_helpers,substitution,pretty_print}.py.
These visitors manipulate syntax only; the old evaluator is never called.
"""

from .source import (
    D0ExpVisitor, FreeVariableVisitor, d0exp_fvset, D0Evar, D0Elam, D0Efix,
    D0Elet, D0Eop1, D0Eop2, D0Eapp, D0Eif0, D0Epair, D0Epfst, D0Epsnd,
)
from .terms import FreshNames


class AllNamesVisitor(FreeVariableVisitor):
    def visit_lam(self, e):
        return {e.arg1} | e.arg2.accept(self)

    def visit_fix(self, e):
        return {e.arg1, e.arg2} | e.arg3.accept(self)

    def visit_let(self, e):
        return {e.arg1} | e.arg2.accept(self) | e.arg3.accept(self)


class TransformVisitor(D0ExpVisitor):
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


class SubstitutionVisitor(TransformVisitor):
    def __init__(self, expression, variable, replacement):
        self.target, self.replacement = variable, replacement
        self.replacement_free = d0exp_fvset(replacement)
        names = expression.accept(AllNamesVisitor()) | replacement.accept(AllNamesVisitor())
        self.names = FreshNames(names | {variable})

    def visit_var(self, e):
        return self.replacement if e.arg1 == self.target else e

    def scope(self, binders, body):
        if self.target in binders or self.target not in d0exp_fvset(body):
            return binders, body
        renamed = []
        for name in binders:
            if name in self.replacement_free:
                fresh = self.names.fresh(name)
                body = body.accept(RenameVisitor(name, fresh))
                renamed.append(fresh)
            else:
                renamed.append(name)
        return renamed, body.accept(self)

    def visit_lam(self, e):
        names, body = self.scope([e.arg1], e.arg2)
        return D0Elam(names[0], body)

    def visit_fix(self, e):
        if e.arg1 == e.arg2:
            names, body = self.scope([e.arg2], e.arg3)
            return D0Efix(names[0], names[0], body)
        names, body = self.scope([e.arg1, e.arg2], e.arg3)
        return D0Efix(names[0], names[1], body)

    def visit_let(self, e):
        init = e.arg2.accept(self)
        names, body = self.scope([e.arg1], e.arg3)
        return D0Elet(names[0], init, body)


def substitute_source(expression, variable, replacement):
    return expression.accept(SubstitutionVisitor(expression, variable, replacement))


class PrintVisitor(D0ExpVisitor[str]):
    def visit_int(self, e):
        return str(e.arg1)

    def visit_btf(self, e):
        return "true" if e.arg1 else "false"

    def visit_var(self, e):
        return e.arg1

    def visit_op1(self, e):
        return f"({e.name} {e.arg1.accept(self)})"

    def visit_op2(self, e):
        return f"({e.arg1.accept(self)} {e.name} {e.arg2.accept(self)})"

    def visit_app(self, e):
        return f"({e.arg1.accept(self)} {e.arg2.accept(self)})"

    def visit_lam(self, e):
        return f"(lam {e.arg1}. {e.arg2.accept(self)})"

    def visit_fix(self, e):
        return f"(fix {e.arg1}({e.arg2}). {e.arg3.accept(self)})"

    def visit_let(self, e):
        return f"(let {e.arg1} = {e.arg2.accept(self)} in {e.arg3.accept(self)})"

    def visit_if0(self, e):
        return f"(if {e.arg1.accept(self)} then {e.arg2.accept(self)} else {e.arg3.accept(self)})"

    def visit_pair(self, e):
        return f"(pair {e.arg1.accept(self)} {e.arg2.accept(self)})"

    def visit_pfst(self, e):
        return f"(fst {e.arg1.accept(self)})"

    def visit_psnd(self, e):
        return f"(snd {e.arg1.accept(self)})"


def format_source(expression):
    return expression.accept(PrintVisitor())
