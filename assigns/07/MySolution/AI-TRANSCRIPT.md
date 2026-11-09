# Assignment 7: AI assistance record

## Session overview

- **Tool:** OpenAI Codex.
- **Date:** November 9, 2026.
- **Task:** Build the LAMBDA3 JSON-RPC service, using the feedback and review
  practices from assignments 1–6 to guide implementation and verification.
- **Scope:** Contract, service, automated tests, demonstrations, documentation,
  and a record of encountered problems and subsequent revisions.

## Important prompts and responses

### Prompt 1: Review previous feedback and draft an approach

> assigns 1-6 have their feedback in GRADE FEEDBACK. before starting on assign 7,
> read the feedback for assigns 1-6 and then read the instructions for assign 7
> and give an initial draft of how to go about assign 7

Codex read all six feedback files, `Assign07.md`, the supplied tests, and the
relevant LAMBDA3 operations. It drafted a contract-first approach with separate
HTTP, JSON-RPC, and language-adapter responsibilities, a terminable interpreter
process, and tests covering successful calls and protocol failures.

### Prompt 2: Implement the assignment

> complete the entire assignment, and i will look over the assignment and check for errors

Codex implemented the service, schemas, tests, demonstrations, and required
documentation under `MySolution/`. The initial verification
passed 16 custom tests and 15 supplied tests.

### Prompt 3: Fix the following errors I found

> look over the work completed for assign 7 and fix the following errors that I found while reviewing the work

Codex implemented the revisions, expanded the tests,
and documented the comparison in `REVIEW.md`.

## Important suggestions and decisions

| Suggestion | Adopted implementation and reason |
| --- | --- |
| Specify the contract before dispatch logic. | Write `RPC.md` first and keep request IDs, errors, batches, notifications, and HTTP outcomes explicit. |
| Keep language semantics in the supplied implementation. | Wrap real LAMBDA3 parsing, type-checking, interpretation, formatting, and compilation without duplicating them. |
| Make interpretation stoppable. | Use a spawned process with a hard deadline; after review, wait for bounded worker exit and read its private temporary JSON result. |
| Verify outputs independently. | Assert expected types and values, compare unchanged compiler output, and test failure behavior separately from successful operations. |
| Keep evidence reproducible. | Declare test dependencies, validate the schema and examples, make demonstrations self-checking, and map requirements to named tests. |

The review Bijan requested led to these changes:

1. Replace the timed pipe poll followed by an unbounded receive with a bounded
   process join and a private temporary JSON result.
2. Log worker crashes and missing or malformed output while returning generic
   internal errors to clients.
3. Correct path redaction for filenames containing spaces and UNC paths.
4. Expand source-limit, mixed-batch, notification, and exact compiler-output
   tests, including successful compilation of a program that would fail if run.
5. Validate the JSON Schema and documented exchanges automatically, and reject
   unexpected demonstration outcomes before saving them.
6. Align setup instructions, architecture descriptions, and test mappings with
   the revised implementation.


`PROBLEMS.md` records the issues and resolutions, including schema-validator
installation and access problems encountered during verification.

## Review and verification

Codex ran HTTP-level tests using real LAMBDA3 for successful language calls,
checked worker termination and recovery, and ran the unmodified course suite
against a real server. All **32 custom tests**, **15 supplied tests**, and
**eight self-checking demonstrations** passed. `TESTING.md` records the
individual checks and observed results. Test doubles are limited to failure
injection and dispatch boundaries.

The language implementation, runtime helpers, standard library, and course
tests are instructor-provided and were not rewritten. Flask is the service
framework; jsonschema is a separate test dependency. Generated programs are
returned as text and never executed by the service.
