# Verification

Observed November 19, 2026: **25 Python tests, 3 Node tests, and 6 real-browser
acceptance checks passed.** Python 3.12.10, Node v24.20.0, Playwright 1.55.0,
Microsoft Edge 157.0.4341.60. No test was skipped in these runs.

Run independently from `assigns/08/`:

```powershell
python -B -m unittest discover -s MySolution/tests -v
node --test MySolution/tests/client.test.cjs
python -B -m MySolution.tests.browser_check
```

The server needs no pip packages. Browser tests additionally need
`python -m pip install -r MySolution/requirements-test.txt` and installed Edge.
Use `--channel chrome` for installed Chrome, or install Playwright Chromium
with `python -m playwright install chromium` and pass `--channel chromium`.
Only Edge was exercised for the recorded results. Tests start and stop their
own local server on an available port; do not start the app first.

## Required-test mapping

| Assign08 required check | Automated evidence | Observed result |
| --- | --- | --- |
| 1. Safety | `test_cps_safety_calls_only_correct_continuation`, `test_cps_trace_and_safety` | Equal columns, both diagonals, empty/safe boards and multi-queen conflicts invoke exactly the correct continuation |
| 2. CPS success/failure/resumption | `test_cps_trace_and_safety`, `test_eight_boards_match_independent_permutation_oracle` | Complete 4×4 and 8×8 traces match an independent eager test oracle, including resumption after solutions |
| 3. All 92, validity, order, uniqueness | `test_all_92_deterministic`, `test_eight_boards_match_independent_permutation_oracle` | Exactly 92 valid distinct boards in independent permutation order; repeated run identical |
| 4. All events and snapshots | Complete trace comparisons above | Correct kind/row/column/board for every event; 33,589 events in 8×8; one final done |
| 5. Genuine laziness | `test_open_does_not_force_and_limit_is_exact`, `test_lazy_thunk_counters_and_memoization`, `test_emit_does_not_run_delayed_failure_until_tail_forced`, `test_unforced_tails_large_boards` | Zero thunk executions at open, memoization, bounded prefixes on 9/10; failing continuation runs only on tail force |
| 6. Lifecycle | `test_lifecycle_and_independence`, `test_expiry_boundary_refresh_and_capacity_recovery`, `test_capacity` | Independent streams, exhausted closure release, repeated next, close, unknown/expired ID, exact inactivity boundary and recovered capacity |
| 7. JSON-RPC | `test_validation_and_ids`, `test_valid_ids_preserved`, `test_nonfinite_ids_rejected`, `test_malformed_envelopes_and_parameter_shapes`, `test_notifications_apply_state_without_response`, `test_transport` | IDs preserved; bad envelopes/parameters rejected; notifications apply state without response bodies; sanitized errors |
| 8. Limits 1/32 | `test_exact_limits_and_final_short_batch`, `test_open_does_not_force_and_limit_is_exact` | No overconsumption; exact ordinary batches and short final batch; immediate done |
| 9. HTTP 8×8 | `test_end_to_end_8` | Real localhost POST flow finds all 92 unique solutions, final done, then empty/done |
| 10. Browser controls/failures | B1–B6 below; three Node client tests | Start/reset, step, play/pause, next solution, completion, RPC/network failures and expiry recovery |

Additional checks: `test_all_sizes_known_solution_counts` finds 2, 10, 4, 40,
92, 352, 724 solutions for sizes 4–10. The supplied interpreter and compiler
agree on the complete 4×4 trace in
`test_interpreter_and_compiler_agree_on_complete_four_trace`.
`test_concurrent_requests_cannot_duplicate_or_skip_events` checks the exact
event multiset from eight callers sharing one stream. Transport checks cover
exponent-overflow IDs, empty/malformed/invalid-UTF8 JSON, invalid numeric
literals, media types, oversized bodies and injected parser recursion failure.

The spec's “same row” case cannot occur under its one-column-per-row invariant.
Equal-column and both diagonal directions are explicitly tested.

## Real-browser evidence

`tests/browser_check.py` prints the browser version, observed behavior per check,
and page errors to the terminal. It does not create submission artifacts.

| Check | Observed behavior |
| --- | --- |
| B1 | Default 8×8; keyboard Start performs no next request; keyboard Step fetches exactly one candidate; textual/accessible coordinates |
| B2 | Real place/reject snapshots; rejection reason in text; distinct candidate state |
| B3 | Keyboard Play/Pause during a deliberately held HTTP call; the in-flight event completes, no further fetch |
| B4 | Keyboard Next solution pauses at a complete board; count increments; desktop/mobile layouts have no horizontal overflow |
| B5 | Backtrack removes one queen; Play finishes 4×4 with exactly two solutions; Step after done is inert; keyboard Reset closes state |
| B6 | Injected RPC/network failures show messages and recover controls; Start succeeds after ID expiry |

Desktop/mobile solution screenshots were visually inspected during development.
Every browser next request uses limit 1. Fault injection is confined
to held-request/outage/expiry scenarios; normal search uses the actual LAMBDA3
service.

Remaining limits: Edge only; no exhaustive accessibility audit or long load test.
Browser completion uses 4×4; the HTTP suite exhausts 8×8.
