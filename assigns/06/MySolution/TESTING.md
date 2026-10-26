# Verification and coverage

Run from `assigns/06/` using Python 3.12 or later:

```text
python -B -m unittest discover -s MySolution/TEST -t . -v
python -B -m MySolution.demo
```

The suite has **49 unittest methods**, with additional subtests
for operators, inputs, scope collisions, invalid forms, and budgets. Test
counts are not the coverage argument; the mapping below identifies the actual
obligations. Expected results are supplied explicitly or computed in test-only
Python oracles, independently of target arithmetic. Terminating examples also
run through the shared source path. Divergent examples are never sent to the
unbounded source evaluator.

| Requirement / acceptance example | Evidence |
| --- | --- |
| TGT-01/02, ACC-13: pure representation and exact printer | `test_terms.TargetOperationsTests.test_exact_printer`; structural `walk` checks |
| TGT-03, ACC-01: capture avoidance, shadowing, replacement preservation | `test_capture_avoidance_independent_of_execution`, `test_substitution_shadowing_and_nested_shadowing`, `test_replacement_is_not_recursively_substituted`, free-variable law checks |
| RED-01/02, ACC-02: weak left-to-right call-by-value, no eta reduction | `TargetEvaluationTests` application traces, divergent-function test, and lambda-body test |
| RED-03/04, ACC-03: zero budget and completion on final step | `test_budget_boundaries`; observation boundary tests are separate |
| RED-05, ACC-04: deterministic reduction and no mutation | Repeated omega runs and input snapshots; compiler helper snapshots every terminating source case |
| ENC-01/04, CMP-03: pure closed library and output, no host execution shortcuts | `test_every_library_combinator_is_closed_and_pure`, `test_target_execution_uses_no_source_arithmetic_or_substitution` |
| ENC-02/03, ACC-05: independent encoding coverage | Naturals 0-4 with successor, predecessor including zero, and zero test; all nine numeric operators on the full 0-3 operand grid; boolean truth tables and projections |
| CMP-04/05/06, ACC-06/07: lexical scope and deterministic freshness | Open expressions, colliding `s/z/t/f/x/thunk_1/thunk_2`, nested shadowing, let initializer, both fix binders, coincident fix binders, input immutability |
| CMP-08, ACC-08: strict contexts versus skipped branches | `test_strict_contexts_and_selected_branches_exhaust`, `test_both_conditional_outcomes_and_short_circuiting_skip_divergence`; source traversal traces |
| CMP-07, ACC-09: complete static rejection | Unsupported forms wrapped in unused conditionals, lambda/fix bodies, boolean operands, and pairs |
| CMP-01/02, QLT-01, ACC-10: visitor compilation without evaluation | Visitor inheritance, patched evaluator that raises if called, compilation of `LOOP`, exact lambda/application translation checks; direct code inspection |
| OBS-01/03, ACC-11: computed values and separate observation budgets | Alpha-renamed literals, arithmetic with redexes under lambdas, zero/false by kind, malformed shapes, exhaustion and exact budget boundary |
| OBS-02, ACC-12: nested pairs | `test_nested_pairs_and_aggregate_budget`, compiler round trip of `((2, true), 3)` |
| DEM-01/02: all fourteen required examples | `test_all_required_demonstrations`, runnable demo and saved pure terms / `results/summary.json` |
| QLT-02/04, ACC-14: module contracts and reproducibility | Documented commands actually executed; evaluator imports no compiler and contains the shared source/target loop |
| SUB-01, QLT-04: standalone packaging | `test_submission.SubmissionTests` loads the bundled AST in an isolated process without Assignment 5; bundled file matches the course file's SHA-256 |
| DOC-01/02/03 | `DESIGN.md`, `README.md`, and `AI-TRANSCRIPT.md`; requirements and editorial review completed |
| DOC-04, ACC-15: slides | `PRESENTATION.pdf` contains 19 pages; all slides passed browser layout checks and their rendered previews were visually inspected |
| DOC-05, ACC-15: recording | **Pending**; must play the actual 15-20 minute face-visible recording and verify instructor access |

## Measurements from the initial run

All 14 mandatory demonstrations passed. In particular:

| Example | Execution beta steps | Observation beta steps | Outcome |
| --- | --- | --- | --- |
| `2 + 3 * 4` | 4 | 25 | 14 |
| `2 - 5` | 87 | 2 | 0 |
| `if true then 1 else LOOP` | 3 | 3 | 1 |
| factorial(4) | 471 | 218 | 24 |
| Fibonacci(5) | 1,794 | 45 | 5 |
| `(lam x. 0) LOOP` | 200 | not run | Execution budget exhausted |
| `LOOP` | 200 | not run | Execution budget exhausted |

Execution counts can be small for arithmetic because weak evaluation returns a
lambda before its Church iteration executes. Observation counts include the
remaining work; the evaluator never normalizes beneath a lambda to decode it.

## Review finding

The first malformed-boolean fixture unexpectedly selected the observer's
identity marker. That is a valid observation result even though the original
term was not a canonical boolean: universal invalid-encoding recognition is
outside scope. The fixture was replaced with a term whose observation produces
neither marker. No observer shortcut or special case was added to accommodate
the test.

The supplied Assignment 5 AST and all earlier assignment submissions were left
unchanged. The bundled source AST has SHA-256
`a1b856205f93822a839ed3e55fb8492c700488e7c51ca8c9e446e7f89e5e549f`, identical
to the original. An additional isolation test verifies that its loader works
when sibling assignments are absent. The full 49-test suite and all 14 demos
passed after this packaging change.

The slide builder checks the complete 19-slide layout before producing the PDF,
validates its PDF header and page count, and exports previews for visual
inspection. The speaking notes provide an 18:05 rehearsal schedule, not a
measured video duration. Passing finite tests is evidence, not a proof of
general semantic preservation. Personal recording and access verification
remain pending.
