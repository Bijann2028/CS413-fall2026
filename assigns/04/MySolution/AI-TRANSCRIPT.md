Assignment 4: AI-assisted implementation

Session overview

Tool: OpenAI Codex.

Task: Complete Assignment 4, following the organization and documentation
style of Assignment 3's submitted MySolution/ files.

Important prompts and responses

Prompt 1: Understand the assignment

look through assign4 and list me the tasks i am to complete

Codex read 04/Assign04.md and 04/lambda1.py and summarized the required MVC
application, real Lint/Interpret, honest placeholders, source editing/state
rules, tests, documentation, and submission contents. It identified that the
supplied file already implements free-variable analysis and evaluation.

Prompt 2: Review the work and draft an initial workflow in the previous submission's style

look at what was submitted for assign3 and follow the same format in drafting a completion for this assignment

Codex read Assignment 3's REQUIREMENTS.md, AI-TRANSCRIPT.md, and assignment
instructions. The resulting structure retained the short prose, tables,
identifiable checks, traceability, and explicit review notes, while following
Assignment 4's required filenames and smaller implementation scope. Assignment
3's proposed saved collections, persistence, and compiler-dependent features
were excluded.

Significant implementation suggestions

Suggestion

Adopted implementation and reason

Keep model rules independent of the browser.

I implemented a pure Python Model that owns revisions, drafts, results, artifacts, and dirty/busy checks so direct requests cannot bypass state guards.

Coordinate the replaceable backend in the controller.

I used constructor injection to permit dispatch/failure tests without changing view code.

Validate Python constructor syntax rather than execute uploaded programs.

I implemented an AST reader that allowlists concrete D0E constructors, validates types/arity, and rejects arbitrary calls, attributes, and scripts.

Bound actual language work in separate processes.

I implemented real Lint/Interpret with a 3-second subprocess timeout and used a background controller thread to keep status requests responsive.

Separate Lint closure checks from runtime behavior.

I kept the operations independent so closed expressions such as division by zero can pass Lint and fail Interpret.

Keep future operations honest.

I kept Type-check/Compile as not_implemented; no compiled artifact is fabricated and Execute remains unavailable.

Record observed verification rather than proposed results.

I distinguished executed unit/integration and real Edge checks from the future compiler/runner contract.

Review and verification

I checked the supplied instructions against the implementation and F1–F10
traceability, ran 24 automated tests, and executed 10 real browser scenarios.

During the first language test run, I found a missing parenthesis in the
factorial sample. I corrected the sample and reran the suite successfully.
Browser checks then confirmed literal HTML-like text, keyboard controls, source
rejection, placeholder outcomes, busy guards, injected backend failure, real
worker timeout, and successful retry. The browser version and observations are
recorded in TEST/browser-results.json and TESTING.md.

During the first clean-archive browser run, I found that Windows CRLF uploads
were incorrectly treated as dirty after the textarea normalized them to LF. I
fixed this by normalizing model source/draft line endings, added a controller
regression test, and changed the browser upload scenario to exercise CRLF
explicitly.

After implementing these fixes, the corrected source commit e06c27c passed a
fresh dependency installation, 24 automated tests, CLI startup, and all 10
browser scenarios from a clean Git archive and isolated virtual environment.
TEST/clean-results.json records this result; the temporary environment was
removed.

Backend substitutes are explicitly limited to dispatch and fault injection.
Arithmetic, factorial, Fibonacci, Lint, runtime failures, and subprocess
timeouts use the real language adapter. lambda1.py is copied unchanged.