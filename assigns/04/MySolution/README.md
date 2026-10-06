# Assignment 4: an MVC web front-end for LAMBDA

## Purpose and scope

This application gives a single local user a browser editor for constructor
expressions from the supplied LAMBDA system. Lint checks free variables;
Interpret evaluates the applied expression. Type-check and Compile explicitly
report that they are not implemented. Execute is reserved for generated code
and remains disabled because no compiler artifact exists.

The documentation follows Assignment 3's short explanations, responsibility
tables, identifiable checks, traceability, and separate AI transcript. The
scope follows Assignment 4: saved collections, accounts, public hosting, and
persistence across server restarts are excluded. Assignment 3's proposed
compiler workflows and assumptions are not treated as implemented features.

| File or directory | Purpose |
| --- | --- |
| `app.py` | Flask HTTP routes, application factory, loopback startup |
| `model.py`, `contracts.py` | Source/draft state, revisions, results, artifacts, backend contract |
| `controller.py` | Source workflow, backend dispatch, background completion |
| `backend.py`, `reader.py`, `worker.py` | Restricted input reader and bounded real language operations |
| `lambda1.py` | Unmodified copy of the instructor's supplied interpreter |
| `templates/`, `static/` | Browser view and interaction forwarding |
| `samples/` | Factorial, Fibonacci, undeclared-variable, malformed, runtime-error, and looping inputs |
| `TEST/` | Automated tests, browser checks, and recorded browser results |
| `ARCHITECTURE.md`, `TESTING.md`, `AI-TRANSCRIPT.md` | Design, verification, traceability, and AI assistance |

## Setup and use

Use **Python 3.12 or later**. Verification used Python **3.12.10**, Flask
**3.1.2**, Playwright **1.55.0**, and Microsoft Edge **154.0.4258.53** on
Windows 11. Flask provides routing, JSON responses, and template/static-file
delivery. Python's standard-library `unittest` runs the non-browser tests.
Playwright is needed only for automated browser checks.

From the repository root, run these commands in PowerShell:

```powershell
cd assigns/04/MySolution
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000/**. Stop the server with Ctrl+C. If port 5000 is
occupied, run `app.py --port 5001` and open http://127.0.0.1:5001/ instead.
The server binds only to loopback and runs without debug mode or the reloader.
It is Flask's local development server, suitable for this assignment's scope.

On macOS/Linux, use `python3` to create the virtual environment and
`.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

## Tests

From `assigns/04/MySolution/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s TEST -p "test_*.py" -v
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv\Scripts\python.exe TEST/browser_smoke.py
```

The browser test starts and stops its own loopback server on a free port; an
already running application is not required. It uses an installed Microsoft
Edge in headless mode. If Chrome is installed instead, run
`TEST/browser_smoke.py --channel chrome`. A separate browser download is not
needed with either installed channel. The screenshot under `test-results/`
is a local verification artifact and is excluded from Git. See `TESTING.md`
for observed results, failure injection, and the F1–F10 mapping.

## Demonstration

| Check | Steps | Expected result |
| --- | --- | --- |
| D1: recursive examples | In Load source choose Factorial (canned), then Lint and Interpret. Repeat with Fibonacci (canned). | No free variables; `D0Vint(arg1=120)` and `D0Vint(arg1=55)`. Each selection creates a revision and clears earlier results. |
| D2: undeclared variable | Choose Manual input; type `D0Evar("x")`; Apply changes; Lint. Replace the text with `D0Eint(42)`, apply, and lint again. | First result is `language_error` listing x. The edited closed expression passes. Tool buttons and source replacement are blocked until changes are applied or discarded. |
| D3: Lint versus Interpret | Enter `D0Eop2("/", D0Eint(1), D0Eint(0))`; apply; Lint; Interpret. | Lint passes because the expression is closed. Interpret reports `runtime_error` with `ZeroDivisionError`. |
| D4: future operations | With applied source, select Type-check and Compile; inspect Execute and its explanatory text. | Both results say `not_implemented`; Execute remains disabled because no generated artifact exists. |
| D5: recovery | Edit an applied program to whitespace and try Apply changes. Inspect the editor and revision; Discard changes, then Interpret. | Rejection preserves applied source and results, keeps the rejected draft for correction, and allows recovery. |

You can type immediately into the initial editor without uploading a file.
Choose File exposes a labeled file input and Load selected file button. The
upload is copied into application state; editing it never writes to the local
file. Manual input opens a blank draft while preserving the applied source
until Apply succeeds. Discard restores the applied source.

## Supported input and execution bounds

Input is **one Python constructor expression producing `d0exp`**, with no
imports or assignments. The reader inspects Python's AST and constructs only
these allowlisted expression classes:

```text
D0Eint, D0Ebtf, D0Evar, D0Eop1, D0Eop2, D0Elam, D0Efix,
D0Eapp, D0Eif0, D0Elet, D0Epair, D0Epfst, D0Epsnd
```

Use positional arguments of the types declared in `lambda1.py`. Strings,
integers (including signed integers), and `True`/`False` are permitted literal
arguments; Boolean values are not accepted as integer arguments. Nested
constructors, parentheses, comments, and multiline expressions are supported.
Keyword arguments, arbitrary calls, attribute access, imports, comprehensions,
and Python arithmetic in constructor arguments are rejected. `D0E000()` is
the interpreter's base class, not an accepted program constructor. The
supported unary operators are `+1` and `-1`; binary operators are `+`, `-`,
`*`, `/` (integer division), `<`, `>`, `<=`, `>=`, `==`, and `!=`.

Source is limited to **65,536 UTF-8 bytes**. HTTP requests have a separate
**1 MiB** transport limit. Empty/whitespace source is rejected. Syntax and
constructor argument errors are diagnosed when Lint or Interpret reads the
applied text, allowing the editor to hold malformed programs for investigation.
The reader allows at most **4,096 AST nodes** and **100 constructor nesting
levels**. Successful value output is truncated after **16,384 characters**.
Accepted text normalizes Windows CRLF and CR line endings to LF to match the
browser editor; the original uploaded file is never modified.

Each real Lint/Interpret operation runs in a separate Python process with a
**3-second subprocess timeout**. On expiration Python kills and waits for that
worker, and the controller publishes `timeout` and restores controls. Process
startup/termination and browser polling add small overhead; this is not a
real-time deadline. Python's recursion limit may report a runtime error before
the timeout. The browser uses asynchronous requests and can remain responsive
during work; source edits, replacements, and conflicting tool actions are
blocked. There is no arbitrary Python or shell execution of uploaded text.

## Known limitations

This is an in-memory, single-user, single-editor-tab application. All clients
connected to one server share its state; simultaneous tabs are outside scope.
Unsent browser edits are not guaranteed to survive page reload or connection
loss. File rejection preserves the applied source; a rejected local file
remains selected for replacement or correction on the user's computer. No
type checker, compiler, generated-code runner, persistence, export workflow,
or public hosting is included. Timeout bounds elapsed worker execution, not
memory usage. The supplied interpreter determines runtime semantics and uses
Python recursion and integers. Browser automation was verified on Edge;
Chrome support is offered by the test script but was not separately verified.

## Reflection: AI-assisted draft for student review

MVC helped make source changes and operation results easier to reason about.
The model owns the applied source, draft, revision, results, and artifact, so
the rules do not depend on whether a request comes from a browser or a test.
A rejected edit leaves the applied source intact, and accepting a new revision
clears old results in one place. Tests can demonstrate those rules without
starting a server. The separate backend also makes it possible to test
controller dispatch with a recording substitute while using the real
interpreter for language tests.

The hardest separation was handling asynchronous work. The browser needs to
disable controls promptly, but the model must still reject conflicting
requests even if someone bypasses those controls. The controller therefore
starts an operation under the model lock, passes a source snapshot to the
backend, and records completion under the same lock. The view only displays
the resulting state. Keeping draft text synchronized without replacing what
the user is typing also required care: ordinary state updates do not overwrite
the editor, while accepted source changes explicitly refresh it.

A future compiler could fit behind the existing backend contract. Its result
would carry a generated artifact tied to the applied revision, and Execute
would consume that artifact rather than call the interpreter or silently
compile again. The model already invalidates artifacts when source changes
or recompilation starts. This separation makes that extension easier to
review, although a real runner would need additional resource limits and
tests before enabling Execute.
