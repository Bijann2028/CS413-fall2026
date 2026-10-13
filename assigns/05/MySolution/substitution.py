"""Single, capture-avoiding substitution without mutation or evaluation."""
from lambda1_vp import D0Elam, D0Efix, D0Elet, d0exp, d0exp_fvset
from .name_helpers import AllNamesVisitor, FreshNames, RenameVisitor, TransformVisitor


class SubstitutionVisitor(TransformVisitor):
    """Create per-call context with an original expression and replacement.

    Direct use: expression.accept(SubstitutionVisitor(expression, target, replacement)).
    Each accept starts a traversal; construct a new visitor for a new call.
    """
    def __init__(self, expression, variable, replacement):
        self.target = variable
        self.replacement = replacement
        self.replacement_fv = d0exp_fvset(replacement)
        self.names = FreshNames(expression.accept(AllNamesVisitor()) |
                                replacement.accept(AllNamesVisitor()) | {variable})

    def visit_var(self, e):
        return self.replacement if e.arg1 == self.target else e

    def scope(self, binders, body):
        # Nothing can be inserted in a target-binding or target-free scope.
        if self.target in binders or self.target not in d0exp_fvset(body):
            return binders, body
        renamed = []
        for name in binders:
            if name in self.replacement_fv:
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
            # Both declarations retain the same fresh spelling. All occurrences
            # still resolve to the parameter, as in the original evaluator.
            names, body = self.scope([e.arg2], e.arg3)
            return D0Efix(names[0], names[0], body)
        names, body = self.scope([e.arg1, e.arg2], e.arg3)
        return D0Efix(names[0], names[1], body)

    def visit_let(self, e):
        init = e.arg2.accept(self)
        names, body = self.scope([e.arg1], e.arg3)
        return D0Elet(names[0], init, body)


def d0exp_substitute(expression: d0exp, variable: str, replacement: d0exp) -> d0exp:
    return expression.accept(SubstitutionVisitor(expression, variable, replacement))
