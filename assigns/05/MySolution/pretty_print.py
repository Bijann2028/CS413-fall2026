"""Exact, non-evaluating rendering of the supplied expression AST."""
from lambda1_vp import D0ExpVisitor, d0exp


class PrettyPrintVisitor(D0ExpVisitor[str]):
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

    def visit_lam(self, e):
        return f"(lam {e.arg1}. {e.arg2.accept(self)})"

    def visit_fix(self, e):
        return f"(fix {e.arg1}({e.arg2}). {e.arg3.accept(self)})"

    def visit_app(self, e):
        return f"({e.arg1.accept(self)} {e.arg2.accept(self)})"

    def visit_if0(self, e):
        return f"(if {e.arg1.accept(self)} then {e.arg2.accept(self)} else {e.arg3.accept(self)})"

    def visit_let(self, e):
        return f"(let {e.arg1} = {e.arg2.accept(self)} in {e.arg3.accept(self)})"

    def visit_pair(self, e):
        return f"(pair {e.arg1.accept(self)} {e.arg2.accept(self)})"

    def visit_pfst(self, e):
        return f"(fst {e.arg1.accept(self)})"

    def visit_psnd(self, e):
        return f"(snd {e.arg1.accept(self)})"


def d0exp_pretty(expression: d0exp) -> str:
    return expression.accept(PrettyPrintVisitor())
