# Assignment 7: LAMBDA3 JSON-RPC service

Python 3.12+ is required by the supplied language implementation. Verified with
Python 3.12.10 and Flask 3.1.2 on Windows. All commands below run from `assigns/07/`.
The adjacent provided `LAMBDA3/` directory, including `mylib/`, must be present.

## Setup and startup

```powershell
python -m venv MySolution/.venv
MySolution/.venv/Scripts/python -m pip install -r MySolution/requirements-test.txt
MySolution/.venv/Scripts/python -B -m MySolution
```

The test requirements include Flask and jsonschema 4.23.0; server-only setup can
use `requirements.txt`. On Unix, use `MySolution/.venv/bin/python` instead.
If Flask is already installed,
`python -B -m MySolution` starts the service directly. Endpoint:
`http://127.0.0.1:8000/rpc`. Stop with Ctrl+C. This is a local development server.

## Tests and demonstrations

Use the same virtual-environment interpreter for setup, startup and tests:

```powershell
MySolution/.venv/Scripts/python -B -m MySolution.verify
MySolution/.venv/Scripts/python -B -m MySolution.demo
```

Verification runs our HTTP test-client suite, starts a real server on an available
local port, runs the unmodified course suite, and stops that server even on failure.
To run independently:

```powershell
MySolution/.venv/Scripts/python -B -m unittest discover -s MySolution/tests -v
```

With the server already running in another terminal:

```powershell
MySolution/.venv/Scripts/python -B -m unittest discover -s TEST -v
```

The demo asserts expected outcomes before recording actual exchanges in
`examples/`: factorial evaluates to `720`, an unbound variable returns -32011,
and both compilers return full source strings.
Generated source is returned but **never run by the service**. The library demo
in our tests includes `mylib/list.lam` declarations in a LAMBDA3 `let` expression.

## curl examples

These request files contain full JSON bodies and avoid Windows command-line
quote ambiguity. Use `curl` instead of `curl.exe` on Unix.

```powershell
curl.exe -i http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-binary "@MySolution/examples/health-request.json"
curl.exe -i http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-binary "@MySolution/examples/typecheck-request.json"
curl.exe -i http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-binary "@MySolution/examples/factorial-request.json"
curl.exe -i http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-binary "@MySolution/examples/unbound-variable-request.json"
curl.exe -i http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-binary "@MySolution/examples/compile-request.json"
curl.exe -i http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-binary "@MySolution/examples/compile-javascript-request.json"
```

## Design and limits

```text
HTTP client → app.py (HTTP/JSON) → rpc.py (envelopes/batches)
                                → service.py (validation/adapter)
                                  → provided LAMBDA3/lambda3.py
                                  → worker.py → spawned interpretation process
                                                → private temporary JSON result
```

Default maximum source: 65,536 UTF-8 bytes. Default interpretation deadline:
5 seconds, including process startup, parse/type-check, evaluation, formatting,
result writing, and worker exit. The parent waits for exit with the remaining
deadline, then reads the completed temporary result. Timeout/failure cleanup
terminates and joins the child and removes its temporary directory.
Set `LAMBDA_MAX_SOURCE_BYTES` and `LAMBDA_TIMEOUT_SECONDS` before startup to
override them. A timeout means the deadline elapsed, not proven nontermination.
Typecheck and compilation run in-process; batches run sequentially. There is no
public deployment, account storage, generated-code execution, or cross-call
stream delivery.

See `RPC.md` and `schema.json` for protocol details, `TESTING.md` for verification,
`PROBLEMS.md` for encountered issues, and `AI-TRANSCRIPT.md` for attribution.

