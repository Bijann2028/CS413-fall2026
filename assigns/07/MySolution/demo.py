"""Record real HTTP-level exchanges using Flask's in-process client."""
import json
from pathlib import Path
from .app import create_app


def check_exchange(record, expected):
    """Fail the demonstration rather than recording an unexpected outcome."""
    body = record['response']
    request = record['request']
    if record['http_status'] != 200 or not isinstance(body, dict):
        raise AssertionError('Demo expected an HTTP 200 JSON-RPC response')
    if body.get('jsonrpc') != '2.0' or body.get('id') != request['id']:
        raise AssertionError('Demo response did not preserve its envelope and ID')
    outcome = 'error' if isinstance(expected, int) else 'result'
    if set(body) != {'jsonrpc', 'id', outcome}:
        raise AssertionError('Demo received the wrong RPC outcome')
    if outcome == 'error':
        if body['error'].get('code') != expected:
            raise AssertionError('Demo received an unexpected RPC error code')
    elif request['method'] == 'lambda.compile':
        result = body['result']
        if set(result) != {'target', 'code'} or result['target'] != expected['target']:
            raise AssertionError('Demo compiler result has an unexpected shape or target')
        if not isinstance(result['code'], str) or not result['code'].strip():
            raise AssertionError('Demo compiler did not return generated code')
    elif body['result'] != expected:
        raise AssertionError('Demo result did not match the independently expected value')


def main():
    output = Path(__file__).resolve().parent / 'examples'
    output.mkdir(exist_ok=True)
    client = create_app().test_client()
    factorial = ('let fact : sint -> sint = fix fact(n: sint): sint => '
                 'if n <= 1 then 1 else n * fact(n - 1) in fact(6) end')
    cases = [
        ('health', 'service.health', {}, {'status': 'ok', 'version': '1.0'}),
        ('typecheck', 'lambda.typecheck', {'source': '1 + 2'}, {'type': 'sint'}),
        ('factorial', 'lambda.interpret', {'source': factorial}, {'type': 'sint', 'value': '720'}),
        ('syntax-error', 'lambda.typecheck', {'source': 'if then'}, -32010),
        ('type-error', 'lambda.typecheck', {'source': '1 + true'}, -32011),
        ('unbound-variable', 'lambda.typecheck', {'source': 'missing'}, -32011),
        ('compile', 'lambda.compile', {'source': '1 + 2', 'target': 'python'}, {'target': 'python'}),
        ('compile-javascript', 'lambda.compile', {'source': '1 + 2', 'target': 'javascript'}, {'target': 'javascript'}),
    ]
    for name, method, params, expected in cases:
        request = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': name}
        (output / f'{name}-request.json').write_text(json.dumps(request, indent=2) + '\n', encoding='utf-8')
        response = client.post('/rpc', json=request)
        record = {'request': request, 'http_status': response.status_code,
                  'response': response.get_json()}
        check_exchange(record, expected)
        (output / f'{name}-exchange.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        body = record['response']
        summary = body.get('error', body.get('result'))
        if method == 'lambda.compile':
            summary = {'target': summary['target'], 'code_characters': len(summary['code'])}
        print(f'{name}: HTTP {response.status_code}: {summary}')
    # Keep the contract's full compiler example synchronized with real output.
    root = output.parent
    json.loads((root / 'schema.json').read_text(encoding='utf-8'))
    record = json.loads((output / 'compile-exchange.json').read_text(encoding='utf-8'))
    heading = '\n## Complete Python compilation exchange\n'
    contract = (root / 'RPC.md').read_text(encoding='utf-8').split(heading)[0]
    example = (heading + '\nRequest:\n\n```json\n'
               + json.dumps(record['request'], indent=2)
               + '\n```\n\nResponse (HTTP 200):\n\n```json\n'
               + json.dumps(record['response'], indent=2) + '\n```\n')
    (root / 'RPC.md').write_text(contract + example, encoding='utf-8')


if __name__ == '__main__':
    main()
