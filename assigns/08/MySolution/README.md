# Assignment 8: Animated N-Queens Search

Animated N-Queens search with a genuine CPS solver in `queens.lam`, lazy event
streams, JSON-RPC, and an incremental browser client. The fixed LAMBDA3 program
is type-checked and compiled using the supplied course implementation at startup.
Search logic lives in LAMBDA3; Python only manages transport and stream values.

## Setup and run

Python 3.12+; no pip packages are required. Keep the supplied adjacent
`LAMBDA3/` directory. Run all commands from `assigns/08/`:

```powershell
python -B -m MySolution
```

Open http://127.0.0.1:8000 and stop the server with Ctrl+C. No external accounts,
assets, or services are needed. The server binds to localhost.

Start opens a fresh stream without consuming it. Step shows one event. Play
continues at the selected delay; Pause stops further requests after the current
request. Next solution runs until the next solution and pauses. Reset closes the
stream and clears the board. Start restarts after completion. Size defaults to
8 and supports 4–10. Choose a new size before Start. Coordinates are zero-based.
Candidate colors and the status text distinguish all event kinds. The counter
increments on solutions; completion has a separate message.

## Tests

```powershell
python -B -m unittest discover -s MySolution/tests -v
node --test MySolution/tests/client.test.cjs
python -B -m MySolution.tests.browser_check
```

Node is needed only for client tests (verified with v24.20.0). Python tests were
verified with Python 3.12.10. Real-browser tests additionally require
`python -m pip install -r MySolution/requirements-test.txt` and installed Edge
(the default). See `TESTING.md` for alternative browser setup.
Observed: 25 Python tests, 3 Node tests, and 6 real-browser checks passed.

## RPC examples

POST these JSON bodies to `http://127.0.0.1:8000/rpc` with Content-Type
`application/json`. Substitute the returned UUID into later requests.

```json
{"jsonrpc":"2.0","id":1,"method":"service.health","params":{}}
```
```json
{"jsonrpc":"2.0","id":1,"result":{"status":"ok","version":"1.0"}}
```
```json
{"jsonrpc":"2.0","id":2,"method":"queens.open","params":{"size":8}}
```
```json
{"jsonrpc":"2.0","id":2,"result":{"stream_id":"<uuid>","size":8}}
```
```json
{"jsonrpc":"2.0","id":3,"method":"queens.next","params":{"stream_id":"<uuid>","limit":1}}
```
```json
{"jsonrpc":"2.0","id":3,"result":{"events":[{"event":"try","column":0,"row":0,"board":[]}],"done":false}}
```
```json
{"jsonrpc":"2.0","id":4,"method":"queens.close","params":{"stream_id":"<uuid>"}}
```
```json
{"jsonrpc":"2.0","id":4,"result":{"closed":true}}
```

Notifications omit `id` and return HTTP 204 without a body. Calls and RPC errors
return HTTP 200. Batches are unsupported (-32600). Parameters must match the
documented object shapes exactly. Error codes and lifetime rules are in
`DESIGN.md`. Streams expire after 300 inactive seconds; cleanup happens on RPC
operations. Exhaustion releases solver state but retains a small completion
marker until expiry or close. At most 128 IDs, including markers, are retained.
Requests are limited to 65,536 bytes. HTTP rejects other media types with 415.

## Limitations and attribution

This solution has been reviewed against earlier grading feedback. Real Edge tests
cover keyboard controls, pause during an in-flight request, failures and restart.
Desktop/mobile screenshots were visually inspected. Only Edge was tested; no
full accessibility audit or long load test is claimed. The display updates one
frame per event without tweening. Zero delay still performs one HTTP request per event,
so a complete animation is intentionally slower than the batched test run.
The simple standard-library HTTP server is intended for local development.

The course `eight_queens_stream.lam` supplied the reverse-board representation,
diagonal distance check, and lazy constructor idioms. This solution replaces its
direct-style stream append search with CPS safety, success, and failure
continuations, emitting all six event types. The provided interpreter/compiler
is reused unchanged. Assignment 7's service was reviewed; this solution uses a new
small standard-library transport and dispatcher with no arbitrary-code API.
See `AI-TRANSCRIPT.md` for AI assistance disclosure.
