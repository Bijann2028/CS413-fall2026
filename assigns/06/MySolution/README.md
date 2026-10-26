# Assignment 6: compiling extended LAMBDA

Requires **Python 3.12 or later**. Tested with Python 3.12.10. There are no
third-party dependencies. Run these commands from `assigns/06/`:

```text
python -B -m unittest discover -s MySolution/TEST -t . -v
python -B -m MySolution.demo
```

The source AST is bundled as `MySolution/lambda1_vp.py`, copied byte-for-byte
from `../05/lambda1_vp.py`. The submitted folder works without the sibling
assignments. Neither the bundled file nor the original is modified.
`-B` avoids generating caches.

## Current state

The compiler/evaluation pipeline is implemented. The 49 unittest
methods pass, including parameterized operator and scope checks, and all 14
mandatory demonstrations pass. See [TESTING.md](TESTING.md) for coverage and
[results/summary.json](results/summary.json) for measured demonstration results.

The **19-page [PDF slide deck](PRESENTATION.pdf)** and
[speaker notes / recording guide](PRESENTATION-NOTES.md) are prepared. The
notes target an approximately 18-minute presentation; actual duration must be
measured during rehearsal and recording. The editable slide source is
[presentation/slides.html](presentation/slides.html).

The presentation video is included in the `MySolution/` submission folder:
[Bijan_Nossoughi_Assign06_Presentation.mp4](Bijan_Nossoughi_Assign06_Presentation.mp4).
The accompanying slides are [PRESENTATION.pdf](PRESENTATION.pdf).

## Modules and public interfaces

| Module | Responsibility |
| --- | --- |
| `source.py`, `lambda1_vp.py` | Load the bundled, unchanged course AST |
| `source_ops.py` | Source substitution, name collection, and printing |
| `terms.py` | `Var`, `Lam`, `App`; printer, free variables, substitution, alpha-equivalence |
| `church.py` | Closed target builders, including predecessor and `Z` |
| `compiler.py` | `compile_expr(expression) -> Term`, implemented through `D0ExpVisitor` |
| `evaluator.py` | `evaluate(expression, max_steps=None)` for both source and target |
| `observe.py` | `observe(term, kind, max_steps=10000)` and nested `PairKind` |
| `examples.py`, `demo.py` | Explicit source examples, expected results, reproducible pipeline |

## Rebuilding the slides (optional)

The submitted PDF is ready to use. Rebuilding it requires the optional Python
`playwright` package and a local Chromium, Chrome, or Edge browser; these are
not needed for the compiler, tests, or demos. From `assigns/06/`:

```text
python -B MySolution/presentation/build_pdf.py
```

The builder discovers common local browser paths, or accepts `--browser PATH`.
It uses only local files, audits layout, and writes `MySolution/PRESENTATION.pdf`.
An optional `--preview-dir DIRECTORY` exports screenshots for visual review.

## Results and resource contracts

`evaluate` returns `EvaluationResult(status, value, steps)`. A completed target
result is a lambda; an exhausted result has no value. Source data values remain
source AST nodes, read using `source_data`. With no explicit budget, target
execution defaults to 10,000 beta steps and source execution is unbounded.

`observe` requires `"nat"`, `"bool"`, or `PairKind(left_kind, right_kind)` and
returns `Observation(status, value, steps, message)`. Observation statuses are
`completed`, `exhausted`, and `malformed`. Its step count is the aggregate for
all observation contexts and nested projections. It never uses the execution
budget or guesses the result kind.

The demo uses **20,000 execution steps** for terminating examples, **200** for
expected exhaustion examples, and a separate **10,000 observation steps**.
Measured factorial(4) takes 471 execution and 218 observation steps;
Fibonacci(5) takes 1,794 execution and 45 observation steps. These counts are
implementation results, not universal performance guarantees. Every example
prints its own budgets, outcomes, counts, and explicit expected answer. Pure
terms are saved in `results/*.lambda.txt`; `results/summary.json` is regenerated
by the demo. `--output DIRECTORY` chooses an alternative artifact directory.

## Errors and limitations

`CompilationError` identifies unsupported literals or operators, including in
unused code. `EvaluationError` rejects open execution or stuck source terms.
Negative, noninteger, and boolean budgets raise `ValueError`. Compilation and
substitution accept open expressions even though execution requires closure.
Input shapes and well-typed uses of supported operators follow the assignment's
assumptions; no static type checker, parser, or web interface is included.

The target evaluator uses syntactic substitution, so large terms can grow
expensively. Source visitor operations and nested-pair observation use Python
recursion. Exhaustion means the supplied budget was insufficient, not proven
nontermination. Observers validate their final data shapes but do not recognize
every invalid untyped encoding.

## Attribution

Language rules, required representations, observation spine, and `Z` come from
[Assign06.md](../Assign06.md) and [REQUIREMENTS.md](../REQUIREMENTS.md).
`source_ops.py` adapts Bijan Nossoughi's Assignment 5 `name_helpers.py`,
`substitution.py`, and `pretty_print.py`. The deterministic naming approach
was also adapted for target terms. The course's original evaluator is never
invoked. AI assistance and validation are recorded in
[AI-TRANSCRIPT.md](AI-TRANSCRIPT.md). Design rules and correctness reasoning
are in [DESIGN.md](DESIGN.md).
