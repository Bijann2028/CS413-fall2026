# Assignment 2: pairs and an eight-queens LAMBDA0 translation

## Files

`lambda0.py` is a copy-sized implementation of the starter interpreter.  It
adds `T0Mpair`, `T0Mpfst`, and `T0Mpsnd` cases to size, free-variable,
substitution, and call-by-value evaluation.  A pair is a value only after its
left component and then its right component have been evaluated.  Consequently
`fst(pair(1, 1 / 0))` raises `ZeroDivisionError`, as required.  A projection
of a non-pair raises `TypeError`.

The integer comparison operators (`<`, `>`, `<=`, `>=`, `==`, and `!=`) are
also implemented.  They return `T0Mbtf`, so they can be conditions in
`T0Mif0`.  These are the only primitives used by the queens translation beyond
the starter arithmetic.

`queens_original.dats` is the original ATS2 source from Assignment 1.
`queens_lambda0.py` constructs its closed LAMBDA0 AST and evaluates it; Python
only constructs terms and decodes/checks the final value.

## Translation map

| ATS2 concept | LAMBDA0 representation |
| --- | --- |
| `list0(int)` board | `pair(false, 0)` for nil; `pair(true, pair(row, rest))` for cons |
| `safe` | `T0Mfix` taking candidate, board, and distance (curried) |
| `search` / row trial | nested `T0Mfix` recursive functions |
| `if` | `T0Mif0` |
| list case / head / tail | `T0Mpfst` and `T0Mpsnd` projections |

The board holds one row per column.  `safe` compares squared differences:
`(candidate - old_row)^2 != distance^2`, alongside a separate same-row check.
This rejects equal rows and both diagonals. The translated search tries rows
from zero upward, recurses after a safe choice, and sums one at every complete
board. The ATS2 program prints every board and reports its count; the LAMBDA0
program returns the corresponding count (92 for eight queens). Python also
uses a separate first-solution helper only to display and validate a board.

## Run

Use Python 3.12+ from this directory:

```powershell
py -3.12 -m unittest discover -s MySolution/TEST -v
py -3.12 MySolution/queens_lambda0.py
$env:PYTHONPATH = 'MySolution'; py -3.12 TEST/test01_lambda0.py
```

The first command tests pairs/projections and the LAMBDA0 queens translation.
The last command reruns the supplied starter tests against this submission's
interpreter.

## Review and verification

I reviewed every AST operation to ensure pairs bind no variables and that
substitution still stops at shadowing lambda/fix binders.  `test02_lambda0.py`
checks nested terms, binder behavior, projections, higher-order use, errors,
and evaluation order.  `test03_queens.py` checks the conflict checker, 1- and
4-queen searches, and verifies the returned 8-queen count and a separate
valid board. I ran these tests with Python 3.12.10: all 8 submission tests and
all 27 supplied starter tests passed. The translated program returned the
count `92`; its board-validation helper returned `(0, 4, 7, 5, 2, 6, 1, 3)`.

## AI-assisted development statement

I used AI assistance after first reviewing the assignment requirements and
starter interpreter. My requests focused on implementing pair and projection
support, explaining the purpose of each required component, constructing an
AST-based eight-queens translation, and running the required tests after Python
3.12 was installed. I reviewed the generated code and test results, including
corrections made after execution exposed issues in the empty-list condition and
result decoder. I verified the final version by running both the
assignment-specific tests and the supplied interpreter tests.
