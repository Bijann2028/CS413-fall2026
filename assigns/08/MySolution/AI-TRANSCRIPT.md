# Assignment 8: AI assistance record

## Session overview

- **Tool:** OpenAI Codex.
- **Date:** November 19, 2026.
- **Task:** Implement the animated N-Queens solver with CPS and lazy streams,
  then review it against the assignment instructions and earlier grade feedback.
- **Scope:** Design, LAMBDA3 solver, RPC service, browser client, automated
  tests, required documentation, and subsequent review and submission cleanup.

## Important prompts and responses

### Prompt 1: Implement Assignment 8

**Request summary:** Create the initial draft for the Assignment 8 solution.

Codex read `Assign08.md`, the supplied queens and lazy-stream examples, the
compiler runtime, and the Assignment 7 README. It wrote `DESIGN.md` before
implementing the LAMBDA3 CPS search, fixed-source adapter, HTTP service, browser
client, tests, and documentation under `MySolution/`. The initial verification
passed 9 Python tests and 3 Node tests, including all 92 eight-queens solutions.

### Prompt 2: Review earlier feedback and double-check testing using the following fixes i have found to errors in the submission (Attached were a list of errors in the work)

Codex read the six available grading reports and reran the original tests.
It compared the implementation with the assignment contract, added independent
oracles and real-browser checks, and fixed defects the original tests missed.
The expanded verification passed 25 Python tests, 3 Node tests, and 6 Edge
browser checks.

## Important suggestions and decisions

| Suggestion | Adopted implementation and reason |
| --- | --- |
| Specify continuation and event contracts before implementation. | Write `DESIGN.md` first, with board invariants, success/failure continuations, event schemas, RPC examples, and lifecycle rules. |
| Keep search semantics in LAMBDA3. | Use CPS safety, success, and failure continuations in `queens.lam`; Python type-checks and compiles only that fixed source and adapts its events. |
| Suspend work across event boundaries. | Wrap each event tail and the initial search dispatch in lazy constructors so opening or reading a prefix does not enumerate later branches. |
| Verify results independently. | Compare against permutation and event-trace oracles, check interpreter/compiler agreement, and use observable thunk counters and a deliberately failing delayed tail. |
| Test real client behavior. | Exercise the actual local service in Edge, including keyboard controls, in-flight pause, completion, failure messages, and restart after expiry. |
| Keep submission contents focused and reproducible. | Retain required code, tests, dependencies and documentation; record observed results in `TESTING.md` and print browser results to the terminal. |

The review Bijan requested led to these changes:

1. Reject nonfinite numeric request IDs, fixing a serialization failure that
   previously disconnected requests containing an ID such as `1e400`.
2. Replace weak delayed-tail evidence with observable thunk counts, memoization
   checks, and a failing continuation that runs only when its tail is forced.
3. Add direct CPS safety tests, independent full-trace and solution comparisons,
   supported-size counts, concurrency checks, and lifecycle/HTTP boundary tests.
4. Return a JSON-RPC parse error for empty JSON bodies and sanitize parser
   recursion failures; the latter path is tested with injected `RecursionError`.
5. Add textual rejection reasons and accessible board summaries, and expand
   dense client code to make state transitions easier to inspect.
6. Align setup instructions, design descriptions, and test mappings with the
   revised implementation and the final submission contents.

## Review and verification

Codex type-checked the solver and exercised the actual LAMBDA3 implementation
through compiled execution and a complete interpreted 4×4 trace. All **25 Python
tests**, **3 Node tests**, and **6 real-browser acceptance checks** passed.
`TESTING.md` maps requirements to named tests and observed results.

The complete 8×8 trace contains 33,589 events and exactly 92 distinct valid
solutions, matching independent oracles in deterministic order. Sizes 4–10
produce 2, 10, 4, 40, 92, 352, and 724 solutions respectively. The HTTP test
consumes the full 8×8 stream; browser completion uses 4×4 for faster playback.
Desktop and mobile screenshots were visually inspected during development.
Only Edge was browser-tested; no complete accessibility audit or long load
test is claimed.
