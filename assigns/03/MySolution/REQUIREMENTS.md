# Assignment 3: requirements for a LAMBDA testing environment

## Purpose and scope

The system gives course students and the instructor a local browser interface
for editing LAMBDA programs, requesting compilation or execution, understanding
results, and keeping repeatable tests. This document specifies future behavior;
it does not report an implemented system or completed software tests.

| Stakeholder | Main goal |
| --- | --- |
| Students writing programs | Try examples, edit programs, and understand errors. |
| Students modifying the compiler | Repeat saved tests and investigate regressions. |
| Instructor | Demonstrate examples and results during lectures. |
| Compiler provider | Agree on the input/output contract used by the environment. |

Version 1 includes local operation, editing, file import/export, supplied
examples, compile/run requests, optional inspection of compiler artifacts,
saved test collections, and clear failure handling. The environment owns the
editing and testing workflow. The separate compiler owns language processing,
execution semantics, diagnostics, and any AST or generated-code output.

Public hosting, accounts, collaborative editing, compiler development, advanced
IDE features, and built-in sharing are outside version 1. Exporting files can
help users exchange work, but no sharing service is required. Reliable editing,
understandable results, and repeatable tests take priority over visual effects.

## Clarification questions and assumptions

No direct stakeholder answers have been received. The following choices are
working assumptions or proposals, not decisions attributed to the instructor.

| ID | Question and why the answer matters | Working position |
| --- | --- | --- |
| A1 | What program input and operations will the compiler accept? Source notation is unfinished, so this determines what the editor can submit. | Unresolved dependency. Assume an agreed textual representation and separate compile/run operations for planning. Real integration waits for an agreed contract; do not invent a language grammar. |
| A2 | Should work survive only refreshes, or also browser changes and different computers? This sets the persistence boundary. | Assume saved work survives refreshes and restarts in the same browser profile on the same computer. Cross-device synchronization is excluded. |
| A3 | What counts as a matching test result? Exact diagnostic text could change as the compiler evolves. | Assume typed integer/Boolean equality for successful runs and compilation rejection for negative tests. Runtime failures do not satisfy compilation-rejection tests. Diagnostic-text matching is deferred. |
| A4 | What execution limit and stopping behavior are needed? A nonterminating test must not block the whole collection. | Propose a 10-second per-test limit measured from submission to the compiler interface through compilation and execution, excluding time waiting in the collection queue. Propose separate actions to stop the current test and continue, or stop the entire collection. The compiler contract must support stopping compilation/execution and releasing resources. |
| A5 | Which browsers and response targets should version 1 support? These choices make usability and responsiveness verifiable. | Propose current stable Chrome and Firefox at acceptance time, with browser versions recorded. Propose visible feedback within 250 ms for ordinary actions on a recorded course laptop with programs up to 100 KB and collections up to 50 tests. |
| A6 | Which compiler artifacts and diagnostic locations are available? The environment cannot display information the compiler never supplies. | Assume artifacts and source locations are optional, and the compiler advertises its capabilities. Missing information is shown as unavailable. |
| A7 | How should users save, rename, and transfer tests? This determines collection management and what happens after saving fails. | Assume explicit save, unique nonempty test names within a collection, and a documented collection import/export format. Preserve unsaved edits after save failures; automatic recovery of unsaved edits after refresh is excluded. Propose save/discard/cancel choices before an in-app action replaces unsaved editor contents. |
| A8 | How should demonstrations work before integration is ready? Users must be able to distinguish sample responses from real results. | Assume an explicitly selected sample-response mode, visibly labeled throughout. Its results never count as real compiler verification. |

These positions allow the interface requirements to be reviewed now. A1 and
the stopping capability in A4 remain integration blockers. Other proposed
targets need stakeholder confirmation before becoming an agreed baseline.

## Functional requirements

Each row is a separately identifiable requirement. **Must** means essential to
the proposed first version. **Should** means useful but secondary to the core
workflow; any deferral should be recorded. Assumption-based requirements retain
that status until confirmed.

| ID | Priority | Required behavior |
| --- | --- | --- |
| F01 | Must | The environment shall let a user type, paste, and modify program text in an editor. |
| F02 | Must | The environment shall offer selectable starter examples and load an editable copy while keeping the supplied original available for reloading. |
| F03 | Must | The environment shall import a program from a local text file and export the current editor text to a local file. A failed import shall leave the current text intact and display an error. |
| F04 | Must | A compile-only request shall submit a snapshot of the editor contents for compilation without executing the program and display the compilation outcome. |
| F05 | Must | A run request shall submit a snapshot for compilation and execution, display the returned value/output on success, and prevent execution when compilation fails. |
| F06 | Should | The environment shall let users reveal available compiler artifacts on demand, keep them collapsed initially, and identify unsupported artifact views as unavailable. |
| F07 | Must | The environment shall distinguish compilation errors, runtime failures, and environment/connection failures with text labels and available explanations. Reported valid source locations shall navigate to the corresponding request's source snapshot. |
| F08 | Must | A failed compiler request shall preserve editor text and saved tests and allow the user to submit another request after the service becomes available. |
| F09 | Must | The environment shall terminate a test still unfinished 10 seconds after submission to the compiler interface, including compilation and execution, and mark it timed-out. The limit is proposed in A4. Users shall be able to cancel a standalone request, stop the current collection test and continue, or stop the entire collection. Stopping a collection shall cancel its active and unattempted tests while retaining completed results. Cancellation shall stop associated compilation/execution through the compiler interface. |
| F10 | Must | Each displayed result shall identify its submitted source snapshot. When the current text differs, the environment shall mark the result as belonging to an earlier version and allow inspection of that version. |
| F11 | Must | The environment shall let users create, edit, rename, and delete saved tests containing a unique nonempty name, program text, and an expected outcome: a typed integer/Boolean value or compilation rejection. Invalid names or missing expectations shall prevent saving and produce an explanation. |
| F12 | Must | The environment shall run a selected saved collection and classify each completed test against its saved expectation: typed value equality passes value tests; compilation rejection passes rejection tests. A completed compiler outcome that does not match the expectation, including a runtime failure, shall be classified as failed. Timeouts, user cancellations, environment errors, and blocked tests shall have separate statuses rather than count as failed comparisons. |
| F13 | Must | A collection run shall show aggregate counts and per-test statuses, with expected and actual outcomes for investigation. Pending, running, passed, failed, timed-out, canceled, environment-error, and blocked statuses shall be distinguishable. Each test shall have exactly one current status, and status counts shall sum to the collection size; incomplete work shall not be reported as passing. |
| F14 | Must | A test's rejection, runtime failure, timeout, or cancellation using stop-current-test shall not prevent subsequent tests from being attempted unless the user stops the collection. If the compiler becomes unavailable, unattempted tests shall be marked blocked with a reason instead of being silently omitted. |
| F15 | Must | Explicitly saved programs and collections shall remain retrievable after refresh and browser restart in the same profile. A failed save shall report failure, preserve the current in-memory edits, and not indicate that saving succeeded. |
| F16 | Should | The environment shall export and import named test collections using a documented format. Invalid imports or conflicting test names shall be reported without overwriting existing saved work. |
| F17 | Must | Sample-response mode shall visibly label its mode and every sample result. Sample results shall not appear as outcomes of a real compiler run. |
| F18 | Must | The environment shall use the agreed compiler contract to exchange program snapshots, operation types, request identifiers, results, diagnostics, and supported artifacts. Unsupported operations or incompatible responses shall be reported as interface failures. |
| F19 | Must | Before an in-app action replaces unsaved editor contents, including example selection or file import, the environment shall offer save, discard, and cancel choices. Save shall proceed with replacement only after a successful save; discard shall replace without saving; cancel or a save failure shall preserve the current contents. |

## Quality requirements

The numeric targets below are proposed acceptance targets from A4/A5, not
measurements or promises supplied by the stakeholder.

| ID | Priority | Requirement and assessment |
| --- | --- | --- |
| Q01 | Must | Editing, example selection, compile/run/cancel, saving, and collection execution shall be operable using only a keyboard, with visible focus. A manual keyboard walkthrough shall demonstrate each task. |
| Q02 | Must | Every result and error status shall have a text label that identifies its meaning without relying on color. Review the statuses with color information removed. |
| Q03 | Must | On the A5 workload and recorded laptop/browser, typing, example selection, and request/cancel actions shall show feedback within 250 ms in at least 19 of 20 trials per action, including while a compiler request is active. Compiler completion time is excluded from this feedback target. |
| Q04 | Must | The main workflow in Q01 and saved-work retrieval shall function in both browsers proposed in A5. A new user shall be able to start the local environment and run a supplied example by following the setup instructions without undocumented steps or developer assistance. Record browser versions and any setup obstacle. |

## External interfaces and dependencies

The browser interface provides editing, status messages, optional artifact
views, and collection management. Local files carry program text and exported
collections; the eventual collection format must document names, program text,
expected-outcome types, and format version. Persistence is limited to A2's
same-profile boundary. Clearing browser storage is outside that guarantee.

Before real integration, the compiler provider and interface team must agree
on input notation, compile/run semantics, typed output representation, source
coordinate conventions, diagnostic categories, capability reporting, request
identifiers, and cancellation of both compilation and execution. Requests and responses must be attributable to
the same source snapshot. Neither transport technology nor UI framework is
prescribed. Sample responses may exercise this contract while the compiler is
unavailable, subject to F17. A successful sample demonstration is not evidence
of working compiler integration.

## Acceptance criteria

These are future checks, not executed tests. Use sample responses only where
explicitly identified and repeat integration-dependent checks with the real
compiler before claiming integration acceptance.

| Check / requirements | Starting conditions | Action or input | Observable expected result |
| --- | --- | --- | --- |
| C01 / F01, F02 | A supplied example is available. | Load it, edit its text, then reload the original and choose discard when prompted. | Text can be edited; the original example remains available and reloads unchanged. |
| C02 / F04, F05 | The agreed compiler accepts a known program returning integer 120; compiler calls can be observed. | Compile only, then run the same program. | Compile-only reports success with no execution call. Run reports integer 120. |
| C03 / F07, F12 | A saved test expects compilation rejection; its invalid program has a compiler-reported source location. | Run the test and select its diagnostic location. | Test passes because compilation was rejected; the diagnostic is labeled as a compilation error and selects the matching snapshot location. A runtime failure for the same expectation would fail. |
| C04 / F08 | Editor contains unsaved changes; saved tests exist; compiler is unreachable. | Request a run, then restore service and retry. | An environment error appears, text and saved tests remain intact, and retry can produce a new result. No language error or passing test is inferred from the outage. |
| C05 / F09, F14 | A collection has a nonterminating test followed by a known passing test. Repeat with the first test stuck in compilation instead of execution. | Run each variant using the proposed limit; measure from submission to the compiler interface. | In both variants, the first test is terminated and marked timed-out at the 10-second limit; the second test is attempted and passes. Queue waiting time is excluded. |
| C06 / F09, F14 | A collection has one completed test, one active test, and two queued tests. | First choose stop-current-test. In a separate run from the same conditions, choose stop-collection. Also cancel a standalone request. | Stop-current-test terminates active work, marks that test canceled, and continues with queued tests. Stop-collection terminates active work, marks the active and two queued tests canceled, retains the completed result, and starts no queued tests. Standalone cancellation stops its work and allows a new request. Verify termination through the compiler interface. |
| C07 / F10 | A slow request for source version A is active. | Edit the program to version B before A completes. | The result identifies version A, marks it as older than the editor contents, and lets the user inspect A. |
| C08 / F12, F13 | Collection contains a value test expecting integer 3, a rejection test, and a value test expecting Boolean true. | Return integer 3, compilation rejection, and Boolean false respectively. | Summary shows two passed and one failed; each row shows expected and actual outcomes. |
| C09 / F15 | A program and collection have been explicitly saved. | Refresh, then close and reopen the browser in the same profile. | Both are retrievable with the same contents. In a separate forced-save-failure check, unsaved changes stay in memory and a failure message replaces any success indication. |
| C10 / F17 | Sample-response mode is selected. | Request a result and inspect its display. | Both the mode and result are labeled as sample data; no claim of real compilation appears. |
| C11 / F19 | The editor contains unsaved changes. | Attempt example selection and, separately, valid file import. Repeat each with save, discard, cancel, and a forced save failure. | Save retains the edits in saved work before replacement; discard replaces them; cancel and failed save preserve the editor contents. Failed save shows an error. |
| C12 / F11 | A collection contains a test named factorial. | Attempt to save another test with that name, then an empty name, then a unique name without an expectation; finally supply a unique name and valid expectation. | Invalid attempts show explanations and leave saved tests unchanged. The valid test is saved with its program and expectation. |
| C13 / F13, F14 | Three saved tests exist; the compiler becomes unreachable during the first request. | Run the collection. | The attempted test shows environment-error; the two unattempted tests show blocked with a reason. Counts are one environment-error and two blocked, totaling three, with zero passed or failed comparisons. |

## Traceability

Section names below refer to `../LAMBDA-UI-informal-requirements.md`.
Assumption IDs refer to the clarification table. Each requirement has a source;
additional detail from an assumption remains a proposal.

| Requirement | Brief section or explicit assumption |
| --- | --- |
| F01 | Trying a program: typing and pasting programs |
| F02 | Trying a program: starter examples and keeping originals |
| F03 | Trying a program: existing files and keeping programs; A7 for import failure handling |
| F04 | Trying a program: compilation without execution; A1 |
| F05 | Trying a program: running and seeing an answer; A1 |
| F06 | Trying a program: optional compiler information; A6 |
| F07 | Understanding what happened: error categories and locations; A6 |
| F08 | Understanding what happened: compiler unavailable and retaining work |
| F09 | Understanding what happened: stopping long runs; A4 |
| F10 | Understanding what happened: identifying which version produced a result |
| F11 | Keeping examples as tests: named programs and expectations; A3, A7 |
| F12 | Keeping examples as tests: rerunning and checking results; A3 |
| F13 | Keeping examples as tests: summary and investigation; A3, A4 |
| F14 | Keeping examples as tests: one troublesome test; Understanding what happened: outages; A4 |
| F15 | Keeping examples as tests: refresh and later sessions; A2, A7 |
| F16 | Keeping examples as tests: sharing can wait; A7 proposes file transfer |
| F17 | The compiler is still evolving: clearly identified sample responses; A8 |
| F18 | The compiler is still evolving: coordination and later real integration; A1, A4, A6 |
| F19 | Trying a program: editing and keeping work; A7 proposes replacement protection |
| Q01 | Keeping the project manageable: keyboard operation |
| Q02 | Keeping the project manageable: meaning independent of colors |
| Q03 | Understanding what happened: usable during work; Keeping the project manageable: prompt responses; A5 |
| Q04 | Keeping the project manageable: local setup and ordinary browsers; A5 |

## Review and verification

The following issues were identified and addressed during AI-assisted drafting.
These are document-review corrections, not software bugs discovered by running
an implementation. The student reviewed and adopted the five additional revisions below, suggested
during AI-assisted review; Codex applied the edits. The AI transcript records
this division of work.

| Draft issue | Resolution |
| --- | --- |
| Treating all errors as equivalent could allow an outage or runtime failure to pass a negative test. | F07 separates error categories; F12 accepts only compilation rejection for rejection tests. C03/C04 check the distinction. |
| A late result could appear to describe newly edited source. | F04/F05 use snapshots; F10 and C07 require visible version association. |
| Persistence language could imply unsaved edits survive refresh or work follows users between computers. | A2/A7 and F15 specify explicit saves and the same browser profile; failed saves preserve in-memory edits only. |
| A nonterminating test could make collection completion impossible. | A4 proposes a time limit; F09 requires termination and F14 continued testing. Cancellation support remains an explicit compiler dependency. |
| Browser and speed targets could be mistaken for stakeholder decisions. | A5 labels them as proposals, and Q03 gives measurable workload and trial conditions. |
| Unsaved edits could be lost when an example or import replaced the editor. | A7 and F19 add save/discard/cancel choices and preserve contents after a failed save; C11 checks each choice. |
| Canceling a test and canceling a collection were ambiguous. | F09/F14 distinguish the two actions, preserve completed results, and define remaining-test behavior; C06 checks both. |
| Failed comparisons, timeouts, and blocked tests had inconsistent classification. | F12-F14 separate terminal statuses and require counts to cover every test; C13 checks an outage during a collection. |
| An execution-only timeout left stuck compilation unbounded. | A4/F09 measure the limit from submission through compilation and execution; C05 checks both stages. |
| C04 and C08 cited requirements beyond the actions they checked. | Their references were narrowed; C12 adds explicit test-name/expectation validation, and C13 checks collection outage reporting. |

The draft was checked against the assignment's required sections, requirement
identifiers, source coverage, and acceptance scenarios. No compiler, UI, or
automated software tests were implemented or executed for this assignment.
