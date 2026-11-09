# LAMBDA3 RPC contract, version 1.0

This contract was written before the dispatcher implementation.

POST `http://127.0.0.1:8000/rpc` with `Content-Type: application/json`
(an optional charset parameter is accepted). Responses containing JSON use
`application/json`. Other media types receive HTTP 415; other routes/methods
receive HTTP 404/405. JSON-RPC results and errors, including malformed JSON,
receive HTTP 200. Valid notifications produce HTTP 204 with an empty body.

| Method | Required params (no extra keys) | Result |
| --- | --- | --- |
| service.health | `{}` | `{ "status":"ok", "version":"1.0" }` |
| lambda.typecheck | `{ "source": string }` | `{ "type": string }` |
| lambda.interpret | `{ "source": string }` | `{ "type": string, "value": string }` |
| lambda.compile | `{ "source": string, "target": "python" or "javascript" }` | `{ "target": string, "code": string }` |

All source methods parse and type-check real LAMBDA3 text first. Types use
`format_type`; values use `d0val_format`, including `<lam>` and `<fix>`.
Compiler output is returned unchanged and never executed by the service.
Standard-library declarations can be included in a `let ... in ... end` source.

## Validation, IDs, batches, and limits

An envelope is an object with `jsonrpc: "2.0"`, a string `method`, and optional
`params` and `id`. Unknown envelope fields are ignored. IDs are strings, finite
JSON numbers, or null; booleans, arrays, and objects are invalid IDs. IDs are
echoed without conversion. Explicit null is a call ID, not a notification.
Missing ID denotes a notification only when the envelope is otherwise valid.
Missing params or params other than an object produce -32602 for known methods.
Unknown method lookup precedes method parameter validation.

A response has exactly one of `result` and `error`. Invalid envelopes always
receive -32600 with null ID, even when they contain another candidate ID.
A valid notification is executed but all RPC results/errors are suppressed.
A nonempty batch returns an array excluding valid notifications; invalid items
produce null-ID errors. Clients match responses by ID, not position. An empty
batch returns one error object, not an array. All-notification batches use 204.

Source must be nonblank and at most 65,536 UTF-8 bytes (inclusive), configurable
with `LAMBDA_MAX_SOURCE_BYTES`. Interpretation uses a spawned process with a
5-second hard deadline, configurable with `LAMBDA_TIMEOUT_SECONDS`; the deadline
includes worker startup, parsing, type-checking, evaluation, formatting, writing
the result, and worker exit. The parent waits for worker exit before reading its
private temporary JSON result; it never waits on an unbounded pipe receive.
Temporary results are removed after every outcome. On expiry the process is
terminated and joined. Timeout does not prove
nontermination. Recursion errors are internal errors, not inferred timeouts.
Batch items execute sequentially, each with its own interpretation deadline.

## Errors

| Code | Message/category | data |
| --- | --- | --- |
| -32700 | Parse error: invalid JSON/encoding or nonfinite JSON number | omitted |
| -32600 | Invalid Request | omitted |
| -32601 | Method not found | omitted |
| -32602 | Invalid params | `{ "reason": string }` |
| -32603 | Internal error | omitted; details logged only on server |
| -32010 | LAMBDA syntax error | `{ "diagnostic": string }` |
| -32011 | LAMBDA type error | `{ "diagnostic": string }` |
| -32012 | Execution timeout | `{ "timeout_seconds": number }` |

Language diagnostics are limited to 500 characters. A Windows drive path, UNC
path, or absolute POSIX path causes that path and the remainder of the diagnostic
line to be omitted, covering filenames containing spaces. Tracebacks and
raw unexpected exception messages are never included in RPC responses.

## Complete exchanges

Each request and response below is a complete JSON body (HTTP 200 unless noted).

```json
{"jsonrpc":"2.0","method":"service.health","params":{},"id":"h"}
```
```json
{"jsonrpc":"2.0","id":"h","result":{"status":"ok","version":"1.0"}}
```
```json
{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"1 + 2"},"id":1}
```
```json
{"jsonrpc":"2.0","id":1,"result":{"type":"sint"}}
```
```json
{"jsonrpc":"2.0","method":"lambda.interpret","params":{"source":"6 * 7"},"id":2}
```
```json
{"jsonrpc":"2.0","id":2,"result":{"type":"sint","value":"42"}}
```

The complete compile exchange appears in the final section and is also recorded
in `examples/compile-exchange.json` by the demonstration script.

```json
{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"if then"},"id":3}
```
```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32010,"message":"LAMBDA syntax error","data":{"diagnostic":"Expected an expression (<lambda>, line 1)"}}}
```
Diagnostic wording depends on the parser; the category and shape above are fixed.
```json
{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"1 + true"},"id":4}
```
```json
{"jsonrpc":"2.0","id":4,"error":{"code":-32011,"message":"LAMBDA type error","data":{"diagnostic":"+: expected bool, got sint"}}}
```
```json
[{"jsonrpc":"2.0","method":"service.health","params":{},"id":"a"},{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"true"},"id":"b"},{"jsonrpc":"2.0","method":"service.health","params":{}}]
```
```json
[{"jsonrpc":"2.0","id":"a","result":{"status":"ok","version":"1.0"}},{"jsonrpc":"2.0","id":"b","result":{"type":"bool"}}]
```
```json
[{"jsonrpc":"2.0","method":"service.health","params":{}}]
```
Response: HTTP 204, zero body bytes.

`schema.json` provides JSON Schema definitions for individual envelopes and
batch payloads. Method-specific parameter validation is specified above.
The schema describes well-formed client envelopes; intentionally invalid batch
members still produce error responses as described above. Schema conformance
and the examples are checked by `tests/test_contract.py` using Draft 2020-12.

## Complete Python compilation exchange

Request:

```json
{
  "jsonrpc": "2.0",
  "method": "lambda.compile",
  "params": {
    "source": "1 + 2",
    "target": "python"
  },
  "id": "compile"
}
```

Response (HTTP 200):

```json
{
  "id": "compile",
  "jsonrpc": "2.0",
  "result": {
    "code": "# The emitted program uses Python values for integers, booleans, lists and\n# tuples. Options need a tagged pair so optn_cons(None) remains distinct from\n# optn_nil (None); the private sentinel is created once per generated program.\ndef _lambda_list_cons(head, tail):\n    if not isinstance(tail, list):\n        raise TypeError(\"list_cons: list tail expected\")\n    return [head] + tail\n\ndef _lambda_list_nilq(value):\n    if not isinstance(value, list):\n        raise TypeError(\"list_nilq: list expected\")\n    return len(value) == 0\n\ndef _lambda_list_head(value):\n    if not isinstance(value, list):\n        raise TypeError(\"list_head: list expected\")\n    if not value:\n        raise ValueError(\"list_head: nonempty list expected\")\n    return value[0]\n\ndef _lambda_list_tail(value):\n    if not isinstance(value, list):\n        raise TypeError(\"list_tail: list expected\")\n    if not value:\n        raise ValueError(\"list_tail: nonempty list expected\")\n    return value[1:]\n\ndef _lambda_a1sz_index(array, index):\n    if not isinstance(array, list) or not isinstance(index, int) or isinstance(index, bool):\n        raise TypeError(\"A1sz indexing expects an array and sint index\")\n    if not 0 <= index < len(array): raise IndexError(\"A1sz index out of range\")\n    return index\ndef _lambda_a1sz_getat(array, index): return array[_lambda_a1sz_index(array, index)]\ndef _lambda_a1sz_setat(array, index, value):\n    array[_lambda_a1sz_index(array, index)] = value\n    return ()\ndef _lambda_a1sz_make_ncpy(size, value):\n    if not isinstance(size, int) or isinstance(size, bool): raise TypeError(\"A1sz size must be sint\")\n    if size < 0: raise ValueError(\"A1sz size must be nonnegative\")\n    return [value for _ in range(size)]\ndef _lambda_a1sz_make_nfun(size, fn):\n    if not isinstance(size, int) or isinstance(size, bool): raise TypeError(\"A1sz size must be sint\")\n    if size < 0: raise ValueError(\"A1sz size must be nonnegative\")\n    return [fn(i) for i in range(size)]\n\ndef _lambda_optn_cons(value):\n    return (_lambda_some_tag, value)\n\ndef _lambda_optn_nilq(value):\n    return value is None\n\ndef _lambda_optn_get(value):\n    if value is None or not (isinstance(value, tuple) and len(value) == 2 and value[0] is _lambda_some_tag):\n        raise ValueError(\"optn_get: nonempty option expected\")\n    return value[1]\n\nclass _LambdaLazy:\n    def __init__(self, thunk):\n        self.thunk, self.evaluated, self.value = thunk, False, None\n\ndef _lambda_lazy_make(thunk):\n    if not callable(thunk): raise TypeError(\"lazy_make: thunk function expected\")\n    return _LambdaLazy(thunk)\ndef _lambda_lazy_eval(value):\n    if not isinstance(value, _LambdaLazy): raise TypeError(\"lazy_eval: Lazy value expected\")\n    if not value.evaluated:\n        value.value = value.thunk(())\n        value.evaluated = True\n    return value.value\ndef _lambda_stcn_nil(): return {\"cons\": False}\ndef _lambda_stcn_cons(head, tail):\n    if not isinstance(tail, _LambdaLazy): raise TypeError(\"stcn_cons: lazy stream tail expected\")\n    return {\"cons\": True, \"head\": head, \"tail\": tail}\ndef _lambda_stcn_check(value, name):\n    if not isinstance(value, dict) or \"cons\" not in value: raise TypeError(name + \": Stcn value expected\")\ndef _lambda_stcn_nilq(value):\n    _lambda_stcn_check(value, \"stcn_nilq\")\n    return not value[\"cons\"]\ndef _lambda_stcn_consq(value):\n    _lambda_stcn_check(value, \"stcn_consq\")\n    return value[\"cons\"]\ndef _lambda_stcn_head(value):\n    _lambda_stcn_check(value, \"stcn_head\")\n    if not value[\"cons\"]: raise ValueError(\"stcn_head: nonempty stream constructor expected\")\n    return value[\"head\"]\ndef _lambda_stcn_tail(value):\n    _lambda_stcn_check(value, \"stcn_tail\")\n    if not value[\"cons\"]: raise ValueError(\"stcn_tail: nonempty stream constructor expected\")\n    return value[\"tail\"]\n\ndef _lambda_format(value):\n    if isinstance(value, _LambdaLazy): return \"<lazy>\"\n    if isinstance(value, dict) and \"cons\" in value:\n        if not value[\"cons\"]: return \"stcn_nil()\"\n        return \"stcn_cons(\" + _lambda_format(value[\"head\"]) + \", <lazy>)\"\n    if value is None:\n        return \"optn_nil()\"\n    if isinstance(value, tuple) and len(value) == 2 and value[0] is _lambda_some_tag:\n        return \"optn_cons(\" + _lambda_format(value[1]) + \")\"\n    if isinstance(value, bool):\n        return \"true\" if value else \"false\"\n    if isinstance(value, list):\n        return \"[\" + \", \".join(_lambda_format(item) for item in value) + \"]\"\n    if isinstance(value, tuple):\n        body = \", \".join(_lambda_format(item) for item in value)\n        return \"(\" + body + (\",\" if len(value) == 1 else \"\") + \")\"\n    if callable(value):\n        return \"<lam>\"\n    return str(value)\n\ndef _lambda_print(value):\n    print(_lambda_format(value))\n    return ()\n\n_lambda_some_tag = object()\n\ndef _lambda_main():\n    _v1 = 1\n    _v2 = 2\n    _v3 = (_v1 + _v2)\n    return _v3\n\n_lambda_result = _lambda_main()\n",
    "target": "python"
  }
}
```
