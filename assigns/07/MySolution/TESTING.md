# Verification and traceability

Environment: November 9, 2026, Windows, Python 3.12.10, Flask 3.1.2, and
jsonschema 4.23.0. Install `requirements-test.txt` as described in README.md.
All commands run from `assigns/07/` using that same Python interpreter:

```text
python -B -m MySolution.verify
python -B -m MySolution.demo
```

After the review: **32/32 custom test methods passed**, then **15/15 supplied
black-box test methods passed** against a real loopback HTTP server. Methods
include additional parameterized subtests. The verification command starts and
stops its server. Course implementation and test files are unchanged.

## Assignment requirements

Names below are methods in `tests/test_api.py` unless another file is named.
Each row identifies a separately checkable behavior.

| Requirement | Acceptance check | Observed |
| --- | --- | --- |
| 1. Health/version | test_health_and_id_types | Exact status and version |
| 1. Preserve IDs | test_health_and_id_types | String, integer, fractional number, explicit null |
| 2. Real type-checking | test_formatted_types | sint, bool and tuple types |
| 3. Arithmetic | test_interpret_real_programs | 20+22 = 42 |
| 3. Recursion | test_interpret_real_programs | factorial(6) = 720 |
| 3. Tuple | test_interpret_real_programs | (1, true) value and type |
| 3. Collection | test_interpret_real_programs | [1, 2] value and List[sint] type |
| Standard library | test_standard_library | Provided list.lam; list_length(list_range(1,5)) = 4 |
| 4. Python compile | test_compile_exact_output_both_targets | Nonempty, exact compiler output; target = python |
| 4. JavaScript compile | test_compile_exact_output_both_targets | Nonempty, exact compiler output; target = javascript |
| 5. Syntax errors | test_language_errors_all_source_methods | -32010 across all source methods |
| 5. Type errors | test_language_errors_all_source_methods | -32011 across all source methods |
| 6. Malformed JSON | test_json_and_transport | -32700, null ID; includes invalid UTF-8/nonfinite numbers |
| 6. Invalid envelope | test_invalid_envelopes | -32600, null ID |
| 6. Unknown method | test_parameter_validation | -32601 |
| 6. Absent/wrong params | test_parameter_validation | -32602 |
| 6. Blank/wrong source | test_parameter_validation | -32602 |
| 6. Source-byte boundary | test_source_byte_limit_boundaries | Inclusive limit succeeds; one byte over fails; multibyte source |
| 7. Function value | test_interpret_real_programs | Exact <lam> and <fix>; no closure/environment serialization |
| 8. Unexpected backend failure | test_internal_failure_is_sanitized | -32603, preserved ID, server log, no secret exception text |
| 8. Runtime failure | test_runtime_failure_not_timeout | Division by zero is -32603, not a timeout |
| 8. Timeout | test_timeout_http_and_process_cleanup | -32012, preserved ID, no surviving child, next call succeeds |
| 8. Real-worker deadline | test_real_backend_tiny_deadline | Normal worker under tiny limit returns -32012 |
| 9. Unbound variable | test_language_errors_all_source_methods | -32011 before evaluation/compilation |
| 10. Batch calls | test_batches_and_notifications | Responses matched by ID; notification omitted |
| 10. Invalid batch items | test_batches_and_notifications | Separate -32600/null-ID response per invalid member |
| 10. Empty batch | test_invalid_envelopes | Single error object, not array |
| 10. Notifications | test_batches_and_notifications | Single/all-notification batch: 204, zero body bytes |
| 10. Notification execution | test_notification_runs_service | Dispatch occurs despite suppressed response |
| HTTP/RPC distinction | test_json_and_transport | HTTP 200 RPC errors; 415 media type, 404 route, 405 method |

## Additional review checks

| File / method | Acceptance check | Observed |
| --- | --- | --- |
| test_review.py / test_default_source_limit_all_methods | Every source method at 65,536 bytes and one over | Passed |
| test_review.py / test_oversized_input_never_reaches_backend | Reject before invoking compiler adapter | Passed |
| test_review.py / test_compilation_covers_recursion_closures_and_collections | Both compilers on factorial, closure, tuple, list, and 1/0 | Passed; unchanged compiler output; no generated-code execution |
| test_review.py / test_dead_branch_is_not_evaluated | if true then 42 else 1/0 | Passed: 42 |
| test_review.py / test_large_interpreted_value_is_not_limited_by_pipe_capacity | Actual 30,000-element A1sz result | Passed; full 90,000-character formatted value |
| test_review.py / test_mixed_batch_continues_after_errors_and_matches_values_by_id | Real calls, language error, unknown method, invalid member, notification, explicit null ID | Passed; correct values/errors and response count |
| test_review.py / test_failing_language_notifications_have_no_response | Syntax/type/unbound-variable failures, single and batch | Passed; 204 and empty body |
| test_review.py / test_unknown_method_precedes_parameter_validation | Unknown method with invalid params | Passed: -32601 |
| test_review.py / test_language_diagnostics_redact_paths_with_spaces_and_unc_names | Inject syntax/type errors with Windows, UNC and POSIX paths | Passed; filename and path tail absent |
| test_review.py / test_worker_failures_are_logged_and_sanitized | Nonzero exit, missing output, malformed output | Passed; logged -32603, preserved ID, cleanup |
| test_review.py / test_partial_worker_result_cannot_bypass_deadline | Worker starts result and stalls | Passed; terminated deadline, no surviving child |
| test_contract.py / test_schema_is_valid_and_documented_examples_conform | Draft 2020-12 meta-schema and all JSON examples in RPC.md | Passed |
| test_contract.py / test_schema_rejects_invalid_requests_and_responses | Invalid IDs, version, error code, result/error exclusivity | Passed |
| test_contract.py / test_saved_exchanges_match_live_service | Eight saved exchanges versus actual HTTP client results | Passed |
| test_contract.py / test_schema_accepts_real_mixed_batch_error_responses | Actual mixed-batch response conforms to response schema | Passed |
| test_contract.py / test_demo_rejects_unexpected_results_and_failures | Demo receives wrong result or unexpected RPC error | Passed; demo refuses to record either as success |

## Architecture and test boundaries

```text
Flask POST /rpc [app.py]
  → JSON-RPC envelope/batch handling [rpc.py]
    → method params and LAMBDA3 adapter [service.py]
      → lambda3 parsing/checking/formatting/compilers (in-process for typecheck/compile)
      → worker.py → spawned process → lambda3 parse/check/evaluate/format
                    → private temporary JSON file, read after bounded worker exit
```

All successful language calls use real LAMBDA3. Doubles are limited to failure
injection and dispatch boundaries. Workers are module-level functions compatible
with Windows spawn. The timeout starts before process startup; completion requires
worker exit after writing its result. Cleanup joins/closes the process and removes
the temporary directory for successful, failed, and timed-out calls.

The tiny-deadline test uses the real worker. Blocking/partial-result fixtures test
termination without relying on recursive divergence, which can instead raise
RecursionError. The deliberate division-by-zero test logs a server traceback;
its HTTP response contains only the generic internal error.

The self-checking demo completed eight exchanges: factorial = 720, syntax =
-32010, type/unbound-variable = -32011, Python code = 4,872 characters, JavaScript
code = 4,996 characters. The generated programs are not executed. Full exchanges
are saved in `examples/`; contract tests also compare these with live results.

Limits: local verification only; no public deployment or throughput claim.
The service limits source bytes and interpretation duration, not total HTTP
body size, batch size, or memory consumption. Batch items execute sequentially.
Tests do not claim other operating systems were exercised.
