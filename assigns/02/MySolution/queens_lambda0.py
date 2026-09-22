"""A closed LAMBDA0 backtracking program for the n-queens problem.

Lists are pairs: empty = (false, 0), cons(x, xs) = (true, (x, xs)).
A board is a list of row numbers, with its head belonging to the most
recently placed column.  The search itself below is an AST, not Python.
"""
from lambda0 import *

def v(name): return T0Mvar(name)
def app(fn, arg): return T0Mapp(fn, arg)
def apps(fn, *args):
    for arg in args: fn = app(fn, arg)
    return fn
def op(symbol, left, right): return T0Mop2(symbol, left, right)
def nil(): return T0Mpair(T0Mbtf(False), T0Mint(0))
def cons(head, tail): return T0Mpair(T0Mbtf(True), T0Mpair(head, tail))
def empty(xs): return T0Mif0(T0Mpfst(xs), T0Mbtf(False), T0Mbtf(True))
def head(xs): return T0Mpfst(T0Mpsnd(xs))
def tail(xs): return T0Mpsnd(T0Mpsnd(xs))
def let(name, value, body): return app(T0Mlam(name, body), value)

def make_safe():
    """safe(candidate)(board)(distance): candidate conflicts with no row in board."""
    candidate, board, distance = v('candidate'), v('board'), v('distance')
    delta = op('-', candidate, head(board))
    # Squared differences detect either diagonal without needing an absolute
    # value.  A separate equality check rejects a shared row.
    no_diagonal_conflict = op('!=', op('*', delta, delta), op('*', distance, distance))
    recurse = apps(v('safe'), candidate, tail(board), op('+', distance, T0Mint(1)))
    body = T0Mif0(
        empty(board), T0Mbtf(True),
        T0Mif0(op('==', candidate, head(board)), T0Mbtf(False),
                T0Mif0(no_diagonal_conflict, recurse, T0Mbtf(False))),
    )
    return T0Mfix('safe', 'candidate', T0Mlam('board', T0Mlam('distance', body)))

def make_first_solution(n):
    """solve(column)(board) tries every row and returns nil on failure."""
    column, board, row = v('column'), v('board'), v('row')
    extended = cons(row, board)
    attempt = apps(v('solve'), op('+', column, T0Mint(1)), extended)
    next_row = app(v('try_row'), op('+', row, T0Mint(1)))
    try_body = T0Mif0(
        op('==', row, T0Mint(n)),
        nil(),
        T0Mif0(
            apps(v('safe'), row, board, T0Mint(1)),
            let('result', attempt, T0Mif0(empty(v('result')), next_row, v('result'))),
            next_row,
        ),
    )
    try_rows = T0Mfix('try_row', 'row', try_body)
    body = T0Mif0(op('==', column, T0Mint(n)), board, app(try_rows, T0Mint(0)))
    return T0Mfix('solve', 'column', T0Mlam('board', body))

def make_queens_term(n=8):
    """Return a closed LAMBDA0 term that counts all n-queens solutions."""
    if n < 1: raise ValueError('n must be positive')
    return let('safe', make_safe(), let('count', make_count(n), apps(v('count'), T0Mint(0), nil())))

def make_count(n):
    """count(column)(board) tries every row and sums all successful leaves."""
    column, board, row = v('column'), v('board'), v('row')
    extended = cons(row, board)
    successful_branch = apps(v('count'), op('+', column, T0Mint(1)), extended)
    next_row = app(v('try_row'), op('+', row, T0Mint(1)))
    try_body = T0Mif0(
        op('==', row, T0Mint(n)),
        T0Mint(0),
        T0Mif0(
            apps(v('safe'), row, board, T0Mint(1)),
            op('+', successful_branch, next_row),
            next_row,
        ),
    )
    try_rows = T0Mfix('try_row', 'row', try_body)
    body = T0Mif0(op('==', column, T0Mint(n)), T0Mint(1), app(try_rows, T0Mint(0)))
    return T0Mfix('count', 'column', T0Mlam('board', body))

def decode_board(value):
    """Python observation only: convert an evaluated LAMBDA0 list to a tuple."""
    rows = []
    while isinstance(value, T0Mpair) and isinstance(value.arg1, T0Mbtf) and value.arg1.arg1:
        # This is host-side observation of an already evaluated pair-list;
        # the LAMBDA0 program itself uses head/tail AST projections above.
        item, value = value.arg2.arg1, value.arg2.arg2
        if not isinstance(item, T0Mint): raise TypeError('board row is not an integer')
        rows.append(item.arg1)
    return tuple(reversed(rows))

def find_one_solution(n=8):
    """A helper for board validation; the translated main program counts all."""
    return decode_board(t0erm_cbv_evaluate0(let('safe', make_safe(), let('solve', make_first_solution(n), apps(v('solve'), T0Mint(0), nil())))))

def count_solutions(n=8):
    value = t0erm_cbv_evaluate0(make_queens_term(n))
    if not isinstance(value, T0Mint): raise TypeError('count is not an integer')
    return value.arg1

def is_valid_board(rows):
    return len(rows) == len(set(rows)) and all(0 <= row < len(rows) for row in rows) and all(
        abs(rows[a] - rows[b]) != abs(a - b)
        for a in range(len(rows)) for b in range(a + 1, len(rows))
    )

if __name__ == '__main__':
    board = find_one_solution(8)
    print(board)
    print('valid:', is_valid_board(board))
    print('Total number of solutions:', count_solutions(8))
