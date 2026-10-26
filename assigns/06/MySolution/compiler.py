"""Compositional visitor compiler; this module never imports an evaluator."""

from . import church
from .source import D0ExpVisitor
from .source_ops import AllNamesVisitor
from .terms import Var, Lam, App, Term, FreshNames, all_names, apps


class CompilationError(ValueError):
    """The source contains a literal or operator outside the required language."""


class Compiler(D0ExpVisitor[Term]):
    def __init__(self, expression):
        self.names = FreshNames(expression.accept(AllNamesVisitor()))

    def visit_int(self, e):
        if e.arg1 < 0:
            raise CompilationError(f"negative literal is unsupported: {e.arg1}")
        return church.numeral(e.arg1)

    def visit_btf(self, e):
        return church.boolean(e.arg1)

    def visit_var(self, e):
        return Var(e.arg1)

    def visit_lam(self, e):
        return Lam(e.arg1, e.arg2.accept(self))

    def visit_app(self, e):
        return App(e.arg1.accept(self), e.arg2.accept(self))

    def visit_let(self, e):
        init = e.arg2.accept(self)
        body = e.arg3.accept(self)
        return App(Lam(e.arg1, body), init)

    def visit_fix(self, e):
        # Nested same-name lambdas correctly make the parameter shadow f.
        return App(church.fixed_point(), Lam(e.arg1, Lam(e.arg2, e.arg3.accept(self))))

    def conditional(self, condition, when_true, when_false):
        self.names.reserved.update(all_names(condition) | all_names(when_true)
                                   | all_names(when_false))
        true_name = self.names.fresh("thunk")
        false_name = self.names.fresh("thunk")
        return apps(condition, Lam(true_name, when_true), Lam(false_name, when_false),
                    church.identity())

    def visit_if0(self, e):
        # Translate both branches, even when one will not execute.
        condition = e.arg1.accept(self)
        when_true = e.arg2.accept(self)
        when_false = e.arg3.accept(self)
        return self.conditional(condition, when_true, when_false)

    def visit_op1(self, e):
        if e.name != "not":
            raise CompilationError(f"unsupported unary operator: {e.name!r}")
        return App(church.negation(), e.arg1.accept(self))

    def visit_op2(self, e):
        if e.name not in church.BINARY_BUILDERS and e.name not in ("and", "or"):
            raise CompilationError(f"unsupported binary operator: {e.name!r}")
        left, right = e.arg1.accept(self), e.arg2.accept(self)
        if e.name == "and":
            return self.conditional(left, right, church.boolean(False))
        if e.name == "or":
            return self.conditional(left, church.boolean(True), right)
        return apps(church.BINARY_BUILDERS[e.name](), left, right)

    def visit_pair(self, e):
        return apps(church.pair(), e.arg1.accept(self), e.arg2.accept(self))

    def visit_pfst(self, e):
        return App(church.first(), e.arg1.accept(self))

    def visit_psnd(self, e):
        return App(church.second(), e.arg1.accept(self))


def compile_expr(expression) -> Term:
    """Compile closed or open source syntax without evaluating or mutating it."""
    return expression.accept(Compiler(expression))
