# Assignment 3: AI-assisted requirements development

## Session overview

- **Tool:** OpenAI Codex.
- **Task:** Turn the supplied LAMBDA stakeholder brief into a requirements
  specification, using the concise explanations, tables, and review style of
  Assignment 2's `MySolution/README.md`.
- **Scope:** Documentation and proposed acceptance checks. No software was
  implemented or tested for Assignment 3.

## Important prompts and responses

### Prompt 1: Understand the assignment

> Read through assignment 3 and summarize tasks laid out for me

Codex read `Assign03.md` and `LAMBDA-UI-informal-requirements.md`, summarized the
deliverables and deadline, and explained that this is a requirements-writing
assignment rather than an implementation task.

### Prompt 2: Draft an initial

> look at my solution for assign 2 and follow the same format, in creating an initial draft and outline

Codex read Assignment 2's README and Assignment 1's separate AI transcript.
It followed Assignment 2's short prose, tables, and review section while using
the two filenames required by Assignment 3.

## Student review and final revisions

> these are the changes that i am making to your initial proposal. review and finalize these changes

My review decisions were:

1. Protect unsaved edits before loading another example or importing a program.
   I adopted save/discard/cancel choices so changing examples cannot silently
   erase current work. A7, F19, and C11 record this behavior.
2. Separate stopping one test from stopping the whole collection. Stopping one
   continues the remaining tests; stopping the collection cancels active and
   queued work while keeping completed results. F09/F14 and C06 specify this.
3. Distinguish failed comparisons from timeout, cancellation, environment-error,
   and blocked statuses. F12-F14 now define consistent categories and counts;
   C13 checks collection reporting when the compiler becomes unavailable.
4. Extend the proposed timeout to include compilation as well as execution,
   measured from submission to the compiler interface. A4/F09 and C05 cover a
   stuck compiler as well as a nonterminating program.
5. Correct acceptance-check references that overstated coverage. C04 and C08
   now cite the requirements their actions check; C12 adds invalid test-name
   and missing-expectation checks, and C13 covers collection outage reporting.


## Verification

Codex checked requirement identifiers, traceability coverage, acceptance-check
references, and consistency of the revised save, cancellation, timeout, and
status rules. The acceptance scenarios remain proposed future checks. No UI,
compiler implementation, or software test suite was run for Assignment 3.
The assumptions remain proposals rather than confirmed instructor decisions.
