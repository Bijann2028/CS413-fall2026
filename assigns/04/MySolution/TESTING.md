# Assignment 4: verification and traceability

## Test approach

Verification combines direct model tests, controller tests with injected
backends, Flask test-client checks, real language integration tests, and a
headless browser smoke test. Mock responses check dispatch and recovery only;
they do not replace real Lint or Interpret. The setup/test commands are in
`README.md`. Test code is in `TEST/test_language.py`, `TEST/test_workflow.py`,
and `TEST/browser_smoke.py`.

Initial verification used Python 3.12.10 and Flask 3.1.2 on Windows 11.
All **24 automated tests passed**. The browser run used Playwright 1.55.0
and Microsoft Edge **154.0.4258.53**; all **10 browser scenarios passed**.
`TEST/browser-results.json` records browser/environment details and observed
outcomes. No separate Chrome run or human visual usability study is claimed.

## Automated checks

| Group | Checks and observed result |
| --- | --- |
| `FreeVariablesTests` | Every concrete expression constructor, duplicate names, nested/shadowed/unused bindings, recursion, let initializer scope, both conditional branches, and `frozenset` return values passed. Unsupported base expressions raise an error. |
| `ReaderTests` | Multiline/comments/signed integers accepted. Unsafe syntax, bad arity/types, arbitrary calls, and excessive size/nesting rejected. |
| `BackendTests` | Real arithmetic returned 42; factorial 5/0/1 returned 120/1/1; Fibonacci 10/0/1 returned 55/0/1. Open Lint diagnostics were sorted; an evaluation spy confirmed closed division by zero was not evaluated during Lint. Input/runtime failures and nested-pair sentinels were classified correctly. Placeholders produced no artifact. Real worker timeout and launch failure were reported; retry passed. |
| `ModelTests` | Direct tests without a browser/server verified manual entry, apply/discard, dirty/busy guards, rejected drafts, revision/result/artifact invalidation, unavailable Execute, failed recompilation, and stale artifact rejection. |
| `ControllerTests` | Recording substitute verified four source-operation dispatches without view changes. A blocking failing backend demonstrated busy rejection, preservation, and real retry. A mismatched result became `backend_error`; upload/example replacement rules and Windows newline normalization passed. |
| `HttpTests` | Initial controls/menu/order, manual input, direct requests bypassing disabled controls, invalid UTF-8, unavailable Execute, and transport-size rejection passed using Flask's test client. |

## Browser smoke test

Each scenario starts from the preceding scenario's completed state. B1 starts
with a fresh application and no applied source. The script starts a real local
server, drives DOM controls in Edge, and checks displayed results and state.

| ID | Steps | Expected outcome | Observed outcome |
| --- | --- | --- | --- |
| B1 | Inspect the source menu and action order; choose Manual input; enter arithmetic; Apply; Interpret. | Four source choices; actions ordered correctly; no-source actions disabled; revision 1 returns 42. | Passed: blank editor accepted manual code; result showed success, revision, and 42. |
| B2 | Edit applied source; inspect blocked controls; Discard; edit again; Apply. | Dirty edits block actions/replacement; Discard restores source; Apply increments revision and clears results. | Passed: menu/Lint disabled while dirty; revision 2 had no earlier results. |
| B3 | Load Factorial and Fibonacci in turn; Lint and Interpret each. | Editable examples are closed and return 120 and 55. | Passed: both real Lint and Interpret results matched. |
| B4 | Lint `D0Evar("x")`; edit to a closed expression; then lint/interpret division by zero and interpret a malformed constructor argument. | Undeclared x; closed success; runtime error after Lint success; distinct input error. | Passed: `language_error`, `success`, `runtime_error`, and `input_error` appeared with the expected diagnostics. |
| B5 | Click Type-check and Compile; inspect Execute and its explanation. | Both placeholders say not implemented; Execute unavailable. | Passed: `not_implemented` outcomes and disabled Execute with generated-code explanation. |
| B6 | Apply whitespace; inspect preserved state/draft; Discard; upload invalid UTF-8, oversized input, then a valid CRLF sample. | Rejected edits stay available; failed uploads preserve applied state; Windows source loads without false dirty state. | Passed: revisions/results remained after rejection; valid CRLF `open.lambda` loaded and linted. |
| B7 | Apply multiline source containing an HTML-like variable name; Lint; inspect DOM. | Source/output remain literal; result includes operation/revision/outcome; no injected element/script. | Passed: exact source and diagnostic text; no image element or injected global. |
| B8 | Substitute a backend that waits, inspect busy controls, release it to raise an exception, then restore the real adapter and retry Lint. | Busy text and guards; backend failure preserves source; retry succeeds. | Passed: editing/replacement/actions blocked; `backend_error` shown; real Lint retry passed. Fault injection was intentional. |
| B9 | Reduce the real adapter timeout to 0.001 seconds; Interpret; restore the normal adapter; repeat on the same source. | Worker termination, source preservation, control restoration, successful retry. | Passed: `timeout` followed by real `D0Vint(arg1=42)`. The shortened timeout is test-only; production uses 3 seconds. |
| B10 | Focus editor, type using keyboard, Tab to Apply and press Enter, Tab to Lint and press Enter. | Labeled controls usable with keyboard and text status feedback. | Passed: focus order and actions worked; Lint reported no free variables. |

## F1–F10 traceability

| Requirement | Automated checks | Browser checks |
| --- | --- | --- |
| F1: source menu, upload/manual/examples, name/revision | `HttpTests.test_initial_page_controls_and_manual_without_upload`; `ControllerTests.test_upload_rejection_and_replacement` | B1, B3, B6 |
| F2: editor, apply/discard, dirty guards | `ModelTests.test_manual_edit_apply_discard_and_revision`; `HttpTests.test_dirty_requests_cannot_bypass_model` | B1, B2, B10 |
| F3: invalid/oversized input; preserve applied state/draft | `ReaderTests.test_bounds`; `ModelTests.test_rejected_changes_preserve_applied_state_and_rejected_draft`; upload and transport rejection tests | B6 |
| F4: action order, source requirement, disabled Execute | `HttpTests`; `ModelTests.test_no_source_busy_and_result_contract`; controller dispatch test | B1, B5, B10 |
| F5: real free-variable Lint | `FreeVariablesTests`; `BackendTests.test_lint_closed_open_sorted_frozenset_and_no_evaluation` | B3, B4, B10 |
| F6: real interpretation and error categories | `BackendTests.test_real_arithmetic_factorial_and_fibonacci_base_cases`; input/runtime and timeout tests | B1, B3, B4, B9 |
| F7: honest placeholders and Execute explanation | `BackendTests.test_placeholders_and_no_artifact`; controller dispatch and HTTP unavailable Execute checks | B5 |
| F8: revision and invalidation; preserve rejected state | model accepted/rejected change and artifact tests; upload/replacement test | B2, B3, B6 |
| F9: result identity and literal multiline source/output | backend result/revision assertions and model result-contract checks | B1, B7 |
| F10: busy, bounded work, failure/retry | `ControllerTests.test_busy_failure_and_successful_retry`; model busy checks; backend timeout/launch failure tests | B8, B9 |

## Review corrections

| Issue found during implementation/review | Correction and verification |
| --- | --- |
| The initial factorial sample had one missing closing parenthesis. | Corrected the sample; real factorial and base-case tests and B3 passed. |
| Disabling browser buttons alone would allow conflicting direct HTTP requests. | Model guards reject dirty/busy actions independently; direct model and HTTP tests cover bypass attempts. |
| Replacing editor text on every status response could erase current typing. | Draft responses update state/controls without replacing editor contents; accepted loads/apply/discard explicitly refresh the editor. B2/B6 check preservation. |
| A returned `D0V000()` could be incorrectly displayed as successful output, especially inside nested pairs. | Recursive sentinel detection returns `runtime_error`; backend tests exercise direct and nested-pair failures. |
| Lint success could incorrectly gate or promise successful interpretation. | Actions dispatch independently; Lint only checks closure. The division-by-zero test and B4 demonstrate the distinction. |
| The first clean-archive browser run exposed CRLF source comparing unequal to the textarea's LF contents, leaving tools disabled after upload. | Normalize line endings in the model; add a Windows-upload controller regression test and make B6 upload explicit CRLF bytes. |

## Clean source verification

The final setup check uses a fresh Git archive of the submission and a new
virtual environment, then installs the documented requirements and runs both
test commands. The final observed result is recorded here after that check.
