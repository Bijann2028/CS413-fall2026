# Problem log

## Initial implementation

1. The supplied standard-library test files import `lambda2`, but assignment 7
   supplies `lambda3`. Leave course files unchanged; test library declarations
   through the actual LAMBDA3 RPC adapter in our own suite.
2. Windows multiprocessing uses spawn, so nested worker functions and unguarded
   startup would fail or recursively start servers. Use a module-level worker
   and a guarded CLI entry point.
3. A recursive nonterminating program may raise RecursionError before a timeout.
   Do not mislabel it. Verify deadline enforcement separately with a worker
   fixture that blocks and can be terminated.
4. A large compiler result can fill a multiprocessing pipe. Only interpretation
   uses the worker; its parent polls/receives before joining, avoiding the usual
   join-before-read deadlock. This initial design was replaced during the review
   below because interpretation results can also be large and partial receives
   are not bounded by a preceding poll.
5. Initial test run: 15 passed, one failed because Flask's test client treats
   `json=None` as no body, not the JSON literal null. Corrected the test to
   serialize payloads explicitly; the server correctly distinguished an empty
   malformed body (-32700) from a valid JSON null invalid envelope (-32600).
6. Division by zero is a validly typed program but fails at runtime. It has no
   required separate application code; return -32603, log the exception on the
   server, and verify that the HTTP response contains no exception details.
7. The provided checker reports `1 + true` as `expected bool, got sint`, which
   differs from the initially drafted example wording. Updated RPC.md to match
   observed diagnostics instead of substituting our own type-checker messages.
8. The JSON Schema validator package is not installed. No runtime dependency
   needs it; checked schema JSON parsing and reviewed definitions manually. A
   third-party schema conformance validation was not claimed in the initial
   version. The review below adds that validation and a declared test dependency.
9. A PowerShell inline `python -c` documentation-update command lost its nested
   quotes and failed with SyntaxError before changing files. Moved that work
   into the regular demo module, which now reproducibly updates the complete
   compiler example in RPC.md and parses schema.json without shell quoting.

## Follow-up review issues and resolutions

10. The original pipe poll was timed, but `recv()` could wait beyond that deadline
    for a complete result. Replaced the channel with a private temporary JSON
    result and a timed join covering result writing and worker exit. Added a
    partial-result/stalled-worker regression and a real 30,000-element result test.
11. A worker that exited without sending a result returned an internal error
    without the required server log. Nonzero exits, missing files and malformed
    results now log their failure and return generic -32603. Tests exercise all
    three cases and process cleanup.
12. Diagnostic redaction stopped at spaces and did not cover UNC names. It could
    disclose a filename after the redacted prefix. Redact the path and remainder
    of the diagnostic line; injected syntax/type errors verify no filename tail.
13. Demos could silently record an unexpected error or wrong result. Added
    independent expected outcomes and assertions before saving each exchange.
14. Schema checking was manual and requirements/test commands did not declare a
    validator dependency. Added requirements-test.txt and five contract tests,
    including Draft 2020-12 validation and comparison with live HTTP replies.
15. Installing the schema validator initially failed with socket-access error
    WinError 10013 in the sandbox. Retried with approved elevated access and
    installed jsonschema 4.23.0 into a temporary directory outside the submission.
    The sandbox could not then read those installed files (ImportError reported
    an unknown package location). Verification uses approved access to that
    temporary dependency location; README uses a normal virtual-environment setup.
16. During the worker replacement, inspection caught obsolete pipe cleanup lines
    left at the end of the file. Removed them before running the tests.
17. Verification discarded all real-server logs and could retry an unexpected
    HTTP 200 reply without checking the startup deadline. It now checks the exact
    health response, checks the deadline on every iteration, and shows retained
    server logs if verification fails.
18. The patch tool rejected a combined delete-and-add of TESTING.md in one patch.
    It made no changes. Replaced the file using two sequential patches instead.

## Final reviewed status

All required service behaviors and both test suites pass. The original course
library test imports remain untouched; our own library integration test passes.
All 32 custom tests, including schema validation, and all 15 course tests pass.
REVIEW.md relates each change to the earlier assignments and feedback.
The implementation is for local use, processes batch items sequentially, and
does not impose an overall batch/body-size limit. These are documented scope
limits rather than outstanding required features.
