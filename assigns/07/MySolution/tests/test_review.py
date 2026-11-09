"""Review regressions derived from the contract and earlier grading feedback."""
import multiprocessing as mp
import os
from pathlib import Path
import time
from unittest.mock import patch

from MySolution.service import L
from MySolution.tests.test_api import HttpTestCase
from MySolution.worker import run_interpretation


def crashed_worker(result_path, params):
    os._exit(7)


def missing_result_worker(result_path, params):
    return


def malformed_result_worker(result_path, params):
    Path(result_path).write_text('{', encoding='utf-8')


def partial_result_worker(result_path, params):
    Path(result_path).write_text('{"result":', encoding='utf-8')
    time.sleep(60)


class ReviewTests(HttpTestCase):
    def test_default_source_limit_all_methods(self):
        for method, extra in [('lambda.typecheck', {}), ('lambda.interpret', {}),
                              ('lambda.compile', {'target': 'python'}),
                              ('lambda.compile', {'target': 'javascript'})]:
            with self.subTest(method=method, extra=extra):
                source = '1' + ' ' * 65535
                self.success(self.call(method, {'source': source, **extra}))
                self.error(self.call(method, {'source': source + ' ', **extra}), -32602)

    def test_compilation_covers_recursion_closures_and_collections(self):
        sources = [
            'let f : sint -> sint = fix f(n: sint): sint => if n <= 1 then 1 else n * f(n-1) in f(6) end',
            'lam (x: sint) => x + 1',
            '(1, true)',
            'list_cons(1, list_nil())',
            '1 / 0',  # Successful compilation must not execute this program.
        ]
        for source in sources:
            expression, _ = L.d0exp_parse_and_typecheck(source)
            for target, compiler in [('python', L.d0exp_compile), ('javascript', L.d0exp_compile_js)]:
                with self.subTest(source=source, target=target):
                    result = self.success(self.call('lambda.compile', {'source': source, 'target': target}))
                    self.assertEqual(result, {'target': target, 'code': compiler(expression)})

    def test_dead_branch_is_not_evaluated(self):
        result = self.success(self.call('lambda.interpret', {'source': 'if true then 42 else 1 / 0'}))
        self.assertEqual(result, {'type': 'sint', 'value': '42'})

    def test_large_interpreted_value_is_not_limited_by_pipe_capacity(self):
        result = self.success(self.call('lambda.interpret', {'source': 'a1sz_make_ncpy(30000, 7)'}))
        self.assertEqual(result, {'type': 'A1sz[sint]', 'value': '[' + ', '.join(['7'] * 30000) + ']'})

    def test_mixed_batch_continues_after_errors_and_matches_values_by_id(self):
        def call(method, params, request_id):
            return {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': request_id}
        batch = [
            call('lambda.interpret', {'source': '6 * 7'}, 'answer'),
            call('lambda.typecheck', {'source': '1 + true'}, 'bad-type'),
            {'jsonrpc': '2.0', 'method': 'lambda.typecheck', 'params': {'source': 'missing'}},
            [],
            call('service.health', {}, 0),
            call('lambda.typecheck', {'source': 'true'}, None),
            call('does.not.exist', {}, 'unknown'),
        ]
        response = self.client.post('/rpc', json=batch)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')
        items = response.get_json()
        self.assertEqual(len(items), 6)
        by_id = {item['id']: item for item in items if item['id'] is not None}
        self.assertEqual(by_id['answer']['result'], {'type': 'sint', 'value': '42'})
        self.assertEqual(by_id[0]['result'], {'status': 'ok', 'version': '1.0'})
        self.assertEqual(by_id['bad-type']['error']['code'], -32011)
        self.assertEqual(by_id['unknown']['error']['code'], -32601)
        null_items = [item for item in items if item['id'] is None]
        self.assertEqual(len(null_items), 2)
        self.assertIn({'type': 'bool'}, [item.get('result') for item in null_items])
        self.assertIn(-32600, [item.get('error', {}).get('code') for item in null_items])
        for item in items:
            self.assertEqual(item['jsonrpc'], '2.0')
            self.assertNotEqual('result' in item, 'error' in item)

    def test_failing_language_notifications_have_no_response(self):
        for source in ('if then', '1 + true', 'missing'):
            notification = {'jsonrpc': '2.0', 'method': 'lambda.interpret', 'params': {'source': source}}
            for payload in (notification, [notification]):
                response = self.client.post('/rpc', json=payload)
                self.assertEqual(response.status_code, 204)
                self.assertEqual(response.data, b'')

    def test_language_diagnostics_redact_paths_with_spaces_and_unc_names(self):
        paths = [r'C:\Users\Jane Doe\secret.py', r'\\server\private share\secret.py', '/tmp/private folder/secret.py']
        for error_type in (L.LambdaSyntaxError, L.TypeCheckError):
            for path in paths:
                with self.subTest(error_type=error_type, path=path):
                    with patch('MySolution.service.L.d0exp_parse_and_typecheck',
                               side_effect=error_type('Problem at ' + path)):
                        body = self.error(self.call('lambda.typecheck', {'source': '1'}),
                                          -32010 if error_type is L.LambdaSyntaxError else -32011)
                    self.assertIn('[path omitted]', body['data']['diagnostic'])
                    self.assertNotIn('secret.py', body['data']['diagnostic'])

    def test_worker_failures_are_logged_and_sanitized(self):
        before = {child.pid for child in mp.active_children()}
        for target in (crashed_worker, missing_result_worker, malformed_result_worker):
            with self.subTest(target=target.__name__):
                def failed_run(params, timeout):
                    return run_interpretation(params, timeout, worker_target=target)
                with patch('MySolution.worker.run_interpretation', side_effect=failed_run):
                    with self.assertLogs('MySolution.worker', level='ERROR'):
                        error = self.error(self.call('lambda.interpret', {'source': '1'}), -32603)
                self.assertEqual(error, {'code': -32603, 'message': 'Internal error'})
        self.assertEqual({child.pid for child in mp.active_children()}, before)

    def test_partial_worker_result_cannot_bypass_deadline(self):
        before = {child.pid for child in mp.active_children()}
        started = time.monotonic()
        def partial_run(params, timeout):
            return run_interpretation(params, 1.0, worker_target=partial_result_worker)
        with patch('MySolution.worker.run_interpretation', side_effect=partial_run):
            self.error(self.call('lambda.interpret', {'source': '1'}), -32012)
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual({child.pid for child in mp.active_children()}, before)

    def test_unknown_method_precedes_parameter_validation(self):
        self.error(self.call('unknown.method', None), -32601)

    def test_oversized_input_never_reaches_backend(self):
        with patch('MySolution.service.perform') as perform:
            self.error(self.call('lambda.compile', {'source': '1' * 65537, 'target': 'python'}), -32602)
            perform.assert_not_called()
