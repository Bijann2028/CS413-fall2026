# Assignment 5: pretty printing and capture-avoiding substitution with visitors

## Purpose and scope

This solution adds exact pretty printing and single capture-avoiding
substitution to the supplied LAMBDA AST. Both operations and helper traversals
use the Visitor interface and `accept`. The supplied interpreter and expression
classes in `../lambda1_vp.py` are unchanged.

| File or directory | Purpose |
| --- | --- |
| `pretty_print.py` | `PrettyPrintVisitor` and `d0exp_pretty(expression)` |
| `substitution.py` | `SubstitutionVisitor` and `d0exp_substitute(expression, variable, replacement)` |
| `name_helpers.py` | All-name collection, fresh names, scoped renaming, and shared transformation methods |
| `__init__.py` | Public visitors and entry points |
| `TEST/` | Separate unittest and pytest suites, with shared explicit fixtures |
| `requirements-test.txt` | Pinned pytest dependency |
| `TESTING.md`, `AI-TRANSCRIPT.md` | Verification, coverage, and AI assistance record |

## Setup and use

Use **Python 3.12 or later**. Verification used **Python 3.12.10** and
**pytest 9.1.1** on Windows. The implementation and unittest suite use only
the standard library. Pytest is required for the second suite.

From the repository root, run in PowerShell:

```powershell
cd assigns/05
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r MySolution/requirements-test.txt
```

On macOS/Linux, use `python3` and `.venv/bin/python` instead.
Run examples from `assigns/05/` so Python can import the supplied interpreter
and `MySolution` package. Tests resolve imports relative to their own files.
The assignment-level `.gitignore` excludes the virtual environment and caches.

## Tests

Run each required suite separately from `assigns/05/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s MySolution/TEST -p "test_*_unittest.py" -v
.\.venv\Scripts\python.exe -m pytest MySolution/TEST/test_visitors_pytest.py -v
```

Results: **6 unittest methods passed**, containing subtests over explicit
fixtures; **152 pytest tests passed**. There are 18 printing fixtures and
44 substitution fixtures. Both suites independently check expected outputs,
input preservation, determinism, free variables, and non-evaluation.
The supplied interpreter's **74 tests also passed**. See [TESTING.md](TESTING.md)
for requirement coverage and verification commands.

## Demonstration

Start Python from the assignment directory:

```powershell
.\.venv\Scripts\python.exe
```

Then enter:

```python
from lambda1_vp import D0Eapp, D0Elam, D0Eop2, D0Evar, D0Eint
from MySolution import d0exp_pretty, d0exp_substitute

expression = D0Eapp(
    D0Elam("x", D0Eop2("+", D0Evar("x"), D0Eint(1))),
    D0Eint(4),
)
print(d0exp_pretty(expression))
# ((lam x. (x + 1)) 4)

expression = D0Elam("y", D0Eop2("+", D0Evar("x"), D0Evar("y")))
print(d0exp_pretty(d0exp_substitute(expression, "x", D0Evar("y"))))
# (lam y_1. (y + y_1))

print(d0exp_pretty(D0Eop2("/", D0Eint(1), D0Eint(0))))
# (1 / 0)
```

| Check | Operation | Expected result |
| --- | --- | --- |
| D1: nested printing | Print application of `lam x. x + 1` to `4` | `((lam x. (x + 1)) 4)` |
| D2: no evaluation | Print division by zero | `(1 / 0)` without an exception |
| D3: ordinary substitution | Substitute `x := 3` in `(x + z)` | `(3 + z)` |
| D4: capture avoidance | Substitute `x := y` in `(lam y. (x + y))` | `(lam y_1. (y + y_1))` |
| D5: let scope | Substitute `x := 3` in `(let x = x in (x + y))` | `(let x = 3 in (x + y))` |
| D6: single insertion | Substitute `x := (x + 1)` in `x` | `(x + 1)` |

Direct dispatch also works: `expression.accept(PrettyPrintVisitor())` or
`expression.accept(SubstitutionVisitor(expression, target, replacement))`.
Construct a new substitution visitor per call so reserved names come from
that call's original inputs.

## Fresh-name policy

For a conflicting binder named `b`, try `b_1`, `b_2`, and so on in ascending
order. Choose the first name absent from all variable and binder names in the
original expression and replacement, the target, and previously generated
names. Reserve it immediately. Traverse children left to right; let
initializers precede bodies, and distinct fix function binders precede
parameters. Each entry-point call creates independent state.

When fix names are equal, use one fresh spelling for both declarations.
Occurrences still refer to the parameter, preserving the supplied evaluator's
shadowing behavior. Skip renaming when the target is bound or absent from the
body's free-variable set.

## Known limitations

Python recursion limits the supported AST depth. Repeated free-variable
analysis can make nested substitution take quadratic time. Input validation
is outside scope: names follow the assignment's identifier restrictions and
inputs are supplied expression instances. No parser or user interface is
included.

The operations never mutate inputs. Unchanged subtrees and inserted
replacements may be shared with the result, as permitted by the assignment;
subsequent caller mutation of a shared subtree can affect both references.

## Design explanation

The supplied AST separates expression structure from operations. Each
constructor implements accept by calling the corresponding method on a
D0ExpVisitor. PrettyPrintVisitor specializes that interface with a string
result: child strings combine into the exact required parentheses, spaces,
keywords, and literal spellings. It does not ask the evaluator for values.
SubstitutionVisitor instead returns an expression. TransformVisitor supplies
rebuilding methods for nonbinding constructors, so substitution and renaming
share recursive traversal while retaining separate binding rules.

A substitution visitor carries the target name, replacement expression,
replacement free variables, and a per-call fresh-name generator. Before
traversal, AllNamesVisitor collects every variable and binder name from both
inputs. It extends the supplied free-variable visitor by including binders
rather than removing them. The generator also reserves the target and each
generated name. This prevents a new binder from colliding with an unused
nested declaration or a name created in another branch.

For each binding scope, substitution first checks whether the target is bound
or absent from the body's free variables. In either case the body is reused,
avoiding unnecessary renaming. Otherwise, each binder that occurs free in the
replacement receives a fresh name before substitution proceeds. RenameVisitor
changes the occurrences belonging to that binder and stops at nested
declarations of the same name. A let initializer remains outside its binder's
scope: substitution always visits it, and renaming an outer binder traverses
it even when the nested let shadows the name in its body.

Fix introduces two body bindings. Distinct names are considered in function,
then parameter order. When the names coincide, both retain one consistent
fresh spelling; occurrences continue to resolve to the parameter. Replacement
insertion returns the replacement directly, preventing recursive substitution
inside it. Constructors are rebuilt without field assignments, and permitted
subtree sharing preserves the original inputs during the operation.

Adding another operation requires a new visitor with methods for the existing
constructors; expression classes need no edits. Adding a new constructor is a
broader change: its accept method and the visitor interface must be extended,
and existing visitors must implement that form. The abstract interface helps
expose missing methods. Separate unittest and pytest suites test exact results
and structural preservation, while free-variable equations provide an
additional check that inserted names remain free.
