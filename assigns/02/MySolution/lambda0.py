"""A small call-by-value LAMBDA0 interpreter, extended with pairs."""
from abc import ABC
from dataclasses import dataclass

type nint = int
type sint = int
type strn = str
type tvar = str

@dataclass
class T0M000(ABC):
    ctag = "T0M000"
type t0erm = T0M000

@dataclass
class T0Mvar(T0M000):
    arg1: tvar; ctag = "T0Mvar"
@dataclass
class T0Mlam(T0M000):
    arg1: tvar; arg2: t0erm; ctag = "T0Mlam"
@dataclass
class T0Mfix(T0M000):
    arg1: tvar; arg2: tvar; arg3: t0erm; ctag = "T0Mfix"
@dataclass
class T0Mapp(T0M000):
    arg1: t0erm; arg2: t0erm; ctag = "T0Mapp"
@dataclass
class T0Mint(T0M000):
    arg1: sint; ctag = "T0Mint"
@dataclass
class T0Mbtf(T0M000):
    arg1: bool; ctag = "T0Mbtf"
@dataclass
class T0Mstr(T0M000):
    arg1: strn; ctag = "T0Mstr"
@dataclass
class T0Mop1(T0M000):
    arg1: strn; arg2: t0erm; ctag = "T0Mop1"
@dataclass
class T0Mop2(T0M000):
    arg1: strn; arg2: t0erm; arg3: t0erm; ctag = "T0Mop2"
@dataclass
class T0Mif0(T0M000):
    arg1: t0erm; arg2: t0erm; arg3: t0erm; ctag = "T0Mif0"
@dataclass
class T0Mpair(T0M000):
    arg1: t0erm; arg2: t0erm; ctag = "T0Mpair"
@dataclass
class T0Mpfst(T0M000):
    arg1: t0erm; ctag = "T0Mpfst"
@dataclass
class T0Mpsnd(T0M000):
    arg1: t0erm; ctag = "T0Mpsnd"

def t0erm_size(term: t0erm) -> sint:
    if isinstance(term, (T0Mint, T0Mbtf, T0Mstr, T0Mvar)): return 1
    if isinstance(term, T0Mlam): return 1 + t0erm_size(term.arg2)
    if isinstance(term, T0Mfix): return 1 + t0erm_size(term.arg3)
    if isinstance(term, (T0Mop1, T0Mpfst, T0Mpsnd)): return 1 + t0erm_size(term.arg2 if isinstance(term, T0Mop1) else term.arg1)
    if isinstance(term, (T0Mapp, T0Mop2, T0Mpair)): return 1 + t0erm_size(term.arg1 if not isinstance(term, T0Mop2) else term.arg2) + t0erm_size(term.arg2 if isinstance(term, (T0Mapp, T0Mpair)) else term.arg3)
    if isinstance(term, T0Mif0): return 1 + t0erm_size(term.arg1) + t0erm_size(term.arg2) + t0erm_size(term.arg3)
    raise TypeError(f"t0erm_size({term})")

type fvset = frozenset[str]
def t0erm_fvset(term: t0erm) -> fvset:
    if isinstance(term, (T0Mint, T0Mbtf, T0Mstr)): return frozenset()
    if isinstance(term, T0Mvar): return frozenset((term.arg1,))
    if isinstance(term, T0Mlam): return t0erm_fvset(term.arg2) - {term.arg1}
    if isinstance(term, T0Mfix): return t0erm_fvset(term.arg3) - {term.arg1, term.arg2}
    if isinstance(term, (T0Mop1, T0Mpfst, T0Mpsnd)): return t0erm_fvset(term.arg2 if isinstance(term, T0Mop1) else term.arg1)
    if isinstance(term, (T0Mapp, T0Mop2, T0Mpair)):
        a = term.arg1 if not isinstance(term, T0Mop2) else term.arg2
        b = term.arg2 if isinstance(term, (T0Mapp, T0Mpair)) else term.arg3
        return t0erm_fvset(a) | t0erm_fvset(b)
    if isinstance(term, T0Mif0): return t0erm_fvset(term.arg1) | t0erm_fvset(term.arg2) | t0erm_fvset(term.arg3)
    raise TypeError(f"t0erm_fvset({term})")

def t0erm_subst0(term: t0erm, x0: tvar, tsub: t0erm) -> t0erm:
    """Substitute a closed term; binders shadow x0, so alpha-renaming is unnecessary."""
    if isinstance(term, (T0Mint, T0Mbtf, T0Mstr)): return term
    if isinstance(term, T0Mvar): return tsub if term.arg1 == x0 else term
    if isinstance(term, T0Mlam): return term if term.arg1 == x0 else T0Mlam(term.arg1, t0erm_subst0(term.arg2, x0, tsub))
    if isinstance(term, T0Mfix): return term if x0 in (term.arg1, term.arg2) else T0Mfix(term.arg1, term.arg2, t0erm_subst0(term.arg3, x0, tsub))
    if isinstance(term, T0Mapp): return T0Mapp(t0erm_subst0(term.arg1, x0, tsub), t0erm_subst0(term.arg2, x0, tsub))
    if isinstance(term, T0Mop1): return T0Mop1(term.arg1, t0erm_subst0(term.arg2, x0, tsub))
    if isinstance(term, T0Mop2): return T0Mop2(term.arg1, t0erm_subst0(term.arg2, x0, tsub), t0erm_subst0(term.arg3, x0, tsub))
    if isinstance(term, T0Mif0): return T0Mif0(*(t0erm_subst0(x, x0, tsub) for x in (term.arg1, term.arg2, term.arg3)))
    if isinstance(term, T0Mpair): return T0Mpair(t0erm_subst0(term.arg1, x0, tsub), t0erm_subst0(term.arg2, x0, tsub))
    if isinstance(term, T0Mpfst): return T0Mpfst(t0erm_subst0(term.arg1, x0, tsub))
    if isinstance(term, T0Mpsnd): return T0Mpsnd(t0erm_subst0(term.arg1, x0, tsub))
    raise TypeError(f"subst0({term})")

def t0erm_cbv_evaluate0(term: t0erm) -> t0erm:
    if isinstance(term, (T0Mint, T0Mbtf, T0Mstr, T0Mlam, T0Mfix)): return term
    if isinstance(term, T0Mpair): return T0Mpair(t0erm_cbv_evaluate0(term.arg1), t0erm_cbv_evaluate0(term.arg2))
    if isinstance(term, (T0Mpfst, T0Mpsnd)):
        pair = t0erm_cbv_evaluate0(term.arg1)
        if not isinstance(pair, T0Mpair): raise TypeError(f"projection expects a pair ({pair})")
        return pair.arg1 if isinstance(term, T0Mpfst) else pair.arg2
    if isinstance(term, T0Mapp):
        fn, arg = t0erm_cbv_evaluate0(term.arg1), t0erm_cbv_evaluate0(term.arg2)
        if isinstance(fn, T0Mlam): return t0erm_cbv_evaluate0(t0erm_subst0(fn.arg2, fn.arg1, arg))
        if isinstance(fn, T0Mfix): return t0erm_cbv_evaluate0(t0erm_subst0(t0erm_subst0(fn.arg3, fn.arg2, arg), fn.arg1, fn))
        raise TypeError(f"application expects a lam/fix ({fn})")
    if isinstance(term, T0Mif0):
        cond = t0erm_cbv_evaluate0(term.arg1)
        if not isinstance(cond, T0Mbtf): raise TypeError(f"condition expects a boolean ({cond})")
        return t0erm_cbv_evaluate0(term.arg2 if cond.arg1 else term.arg3)
    if isinstance(term, T0Mop1):
        value = t0erm_cbv_evaluate0(term.arg2)
        if term.arg1 not in ('+', '-') or not isinstance(value, T0Mint): raise TypeError(f"{term.arg1} expects an integer ({value})")
        return T0Mint(value.arg1 if term.arg1 == '+' else -value.arg1)
    if isinstance(term, T0Mop2):
        left, right = t0erm_cbv_evaluate0(term.arg2), t0erm_cbv_evaluate0(term.arg3)
        if not isinstance(left, T0Mint) or not isinstance(right, T0Mint): raise TypeError(f"{term.arg1} expects integers ({left}, {right})")
        ops = {'+': lambda: left.arg1 + right.arg1, '-': lambda: left.arg1 - right.arg1, '*': lambda: left.arg1 * right.arg1, '/': lambda: left.arg1 // right.arg1, '%': lambda: left.arg1 % right.arg1, '<': lambda: left.arg1 < right.arg1, '>': lambda: left.arg1 > right.arg1, '<=': lambda: left.arg1 <= right.arg1, '>=': lambda: left.arg1 >= right.arg1, '==': lambda: left.arg1 == right.arg1, '!=': lambda: left.arg1 != right.arg1}
        if term.arg1 not in ops: raise TypeError(f"t0erm_cbv_evaluate0({term})")
        answer = ops[term.arg1]()
        return T0Mbtf(answer) if isinstance(answer, bool) else T0Mint(answer)
    raise TypeError(f"t0erm_cbv_evaluate0({term})")
