# Assignment 4: AI-assisted implementation

## Session overview

- **Tool:** OpenAI Codex.
- **Task:** Complete Assignment 4, following the organization and documentation
  style of Assignment 3's submitted `MySolution/` files.
- **Scope:** Local MVC application, real Lint/Interpret integration, automated
  tests, browser verification, sample inputs, and required documentation.
- **Authorship:** Codex produced the implementation and initial documentation.
  The reflection in `README.md` is explicitly an AI-assisted draft for student
  review. No student review or personal experience is invented in this record.

## Important prompts and responses

### Prompt 1: Understand the assignment

> look through assign4 and list me the tasks i am to complete

Codex read `04/Assign04.md` and `04/lambda1.py`, summarized the required MVC
application, real Lint/Interpret, honest placeholders, source editing/state
rules, tests, documentation, and submission contents. It identified that the
supplied file already implements free-variable analysis and evaluation.

### Prompt 2: Complete the work in the previous submission's style

> look at what was submitted for assign3 and follow the same format in completing this assignment

Codex read Assignment 3's `REQUIREMENTS.md`, `AI-TRANSCRIPT.md`, and assignment
instructions. It retained the short prose, tables, identifiable checks,
traceability, and explicit review notes, while following Assignment 4's
required filenames and smaller implementation scope. Assignment 3's proposed
saved collections, persistence, and compiler-dependent features were excluded.

## Significant implementation suggestions

| Suggestion | Adopted implementation and reason |
| --- | --- |
| Keep model rules independent of the browser. | Pure Python `Model` owns revisions, drafts, results, artifacts, and dirty/busy checks. Direct requests cannot bypass state guards. |
| Coordinate the replaceable backend in the controller. | Constructor injection permits dispatch/failure tests without changing view code. |
| Validate Python constructor syntax rather than execute uploaded programs. | AST reader allowlists concrete D0E constructors, validates types/arity, and rejects arbitrary calls, attributes, and scripts. |
| Bound actual language work in separate processes. | Real Lint/Interpret use a 3-second subprocess timeout; a background controller thread keeps status requests responsive. |
| Separate Lint closure checks from runtime behavior. | Both operations can run independently; closed division by zero passes Lint and fails Interpret. |
| Keep future operations honest. | Type-check/Compile return `not_implemented`; no compiled artifact is fabricated and Execute remains unavailable. |
| Record observed verification rather than proposed results. | Executed unit/integration and real Edge checks are distinguished from the future compiler/runner contract. |

## Review and verification performed by Codex

Codex checked supplied instructions against the implementation and F1–F10
traceability, ran 24 automated tests, and executed 10 real browser scenarios.
The first language test run found a missing parenthesis in the factorial
sample; Codex corrected it and reran the suite successfully. Browser checks
confirmed literal HTML-like text, keyboard controls, source rejection,
placeholder outcomes, busy guards, injected backend failure, real worker
timeout, and successful retry. The browser version and observations are
recorded in `TEST/browser-results.json` and `TESTING.md`.

The first clean-archive browser run found that Windows CRLF uploads were
incorrectly treated as dirty after the textarea normalized them to LF. Codex
normalized model source/draft line endings, added a controller regression
test, and changed the browser upload scenario to exercise CRLF explicitly.

Backend substitutes are explicitly limited to dispatch and fault injection.
Arithmetic, factorial, Fibonacci, Lint, runtime failures, and subprocess
timeouts use the real language adapter. `lambda1.py` is copied unchanged.

## Student review status

The user requested completion and matching Assignment 3's format. No later
student review decisions have been received in this session. Before handing
in the work, the student should read the implementation, check the reflection
against their own experience, and understand the design and test results.
This note documents authorship; it does not claim that such review occurred.
