import json
import multiprocessing as mp
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from MySolution.app import create_app
from MySolution.errors import RpcError
from MySolution.service import LanguageService, L
from MySolution.worker import run_interpretation


def blocked_worker(result_path, params):
    time.sleep(60)


class HttpTestCase(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def call(self, method, params, request_id="test"):
        return self.client.post('/rpc', json={"jsonrpc": "2.0", "method": method,
                                               "params": params, "id": request_id})

    def success(self, response, request_id="test"):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        body = response.get_json()
        self.assertEqual(set(body), {"jsonrpc", "id", "result"})
        self.assertEqual(body["jsonrpc"], "2.0")
        self.assertEqual(body["id"], request_id)
        return body["result"]

    def error(self, response, code, request_id="test"):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        body = response.get_json()
        self.assertEqual(set(body), {"jsonrpc", "id", "error"})
        self.assertEqual(body["jsonrpc"], "2.0")
        self.assertEqual(body["id"], request_id)
        self.assertIs(type(body["error"]["code"]), int)
        self.assertEqual(body["error"]["code"], code)
        self.assertIsInstance(body["error"]["message"], str)
        self.assertNotIn("Traceback", response.get_data(as_text=True))
        return body["error"]


class ApiTests(HttpTestCase):
    def test_health_and_id_types(self):
        for request_id in (None, 0, -2, 1.25, "abc"):
            with self.subTest(request_id=request_id):
                self.assertEqual(self.success(self.call("service.health", {}, request_id), request_id),
                                 {"status": "ok", "version": "1.0"})

    def test_formatted_types(self):
        for source, typ in [("true", "bool"), ("1+2", "sint"),
                            ("(1, true)", "(sint, bool)")]:
            self.assertEqual(self.success(self.call("lambda.typecheck", {"source": source})),
                             {"type": typ})

    def test_interpret_real_programs(self):
        programs = [
            ("20+22", "sint", "42"),
            ("let fact : sint -> sint = fix fact(n: sint): sint => if n <= 1 then 1 else n * fact(n-1) in fact(6) end", "sint", "720"),
            ("(1, true)", "(sint, bool)", "(1, true)"),
            ("list_cons(1,list_cons(2,list_nil()))", "List[sint]", "[1, 2]"),
            ("lam (x: sint) => x", "sint -> sint", "<lam>"),
            ("fix f(x: sint): sint => x", "sint -> sint", "<fix>"),
        ]
        for source, typ, value in programs:
            with self.subTest(source=source):
                self.assertEqual(self.success(self.call("lambda.interpret", {"source": source})),
                                 {"type": typ, "value": value})

    def test_standard_library(self):
        library = Path(__file__).resolve().parents[2] / "LAMBDA3/mylib/list.lam"
        source = "let\n" + library.read_text(encoding="utf-8") + "\nin list_length(list_range(1, 5)) end"
        self.assertEqual(self.success(self.call("lambda.interpret", {"source": source})),
                         {"type": "sint", "value": "4"})

    def test_compile_exact_output_both_targets(self):
        expression, _ = L.d0exp_parse_and_typecheck("1+2")
        for target, compiler in [("python", L.d0exp_compile), ("javascript", L.d0exp_compile_js)]:
            result = self.success(self.call("lambda.compile", {"source": "1+2", "target": target}))
            self.assertEqual(result, {"target": target, "code": compiler(expression)})
            self.assertTrue(result["code"].strip())

    def test_language_errors_all_source_methods(self):
        for method in ("lambda.typecheck", "lambda.interpret", "lambda.compile"):
            for source, code in [("if then", -32010), ("1+true", -32011), ("missing", -32011)]:
                params = {"source": source}
                if method == "lambda.compile":
                    params["target"] = "python"
                self.error(self.call(method, params), code)

    def test_parameter_validation(self):
        for params in (None, [], "x", {}, {"source": 12}, {"source": " "},
                       {"source": "1", "extra": 0}, {"source": "\ud800"}):
            self.error(self.call("lambda.typecheck", params), -32602)
        for target in (None, [], "ruby", True):
            self.error(self.call("lambda.compile", {"source": "1", "target": target}), -32602)
        self.error(self.call("service.health", {"extra": 1}), -32602)
        self.error(self.client.post('/rpc', json={"jsonrpc": "2.0", "method": "service.health", "id": "test"}), -32602)
        self.error(self.call("SERVICE.health", {}), -32601)

    def test_source_byte_limit_boundaries(self):
        self.client = create_app(LanguageService(max_source_bytes=8)).test_client()
        self.success(self.call("lambda.typecheck", {"source": "1 # éé"}))
        self.error(self.call("lambda.typecheck", {"source": "1 # éé "}), -32602)

    def test_invalid_envelopes(self):
        for payload in (None, 1, "x", {}, [], {"jsonrpc": "1.0", "method": "service.health"},
                        {"jsonrpc": "2.0", "method": 1},
                        *({"jsonrpc": "2.0", "method": "service.health", "id": x} for x in (True, [], {}))):
            with self.subTest(payload=payload):
                self.error(self.client.post('/rpc', data=json.dumps(payload), content_type='application/json'), -32600, None)

    def test_json_and_transport(self):
        for raw in (b'{', b'\xff', b'NaN', b'1e999'):
            self.error(self.client.post('/rpc', data=raw, content_type='application/json'), -32700, None)
        self.assertEqual(self.client.post('/rpc', data='{}', content_type='text/plain').status_code, 415)
        self.assertEqual(self.client.get('/rpc').status_code, 405)
        self.assertEqual(self.client.post('/other', json={}).status_code, 404)
        self.success(self.client.post('/rpc', data=json.dumps({"jsonrpc": "2.0", "method": "service.health", "params": {}, "id": "test"}), content_type='application/json; charset=utf-8'))

    def test_batches_and_notifications(self):
        notification = {"jsonrpc": "2.0", "method": "service.health", "params": {}}
        for payload in (notification, [notification], {**notification, "method": "unknown"},
                        {**notification, "params": []}):
            response = self.client.post('/rpc', json=payload)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.data, b'')
        batch = [{**notification, "id": "a"}, notification, 7,
                 {**notification, "id": 0}, {**notification, "id": True}]
        response = self.client.post('/rpc', json=batch)
        self.assertEqual(response.status_code, 200)
        items = response.get_json()
        self.assertEqual(len(items), 4)
        self.assertEqual({item['id'] for item in items}, {"a", 0, None})
        self.assertEqual(sum(item.get('error', {}).get('code') == -32600 for item in items), 2)

    def test_notification_runs_service(self):
        with patch.object(LanguageService, 'call', return_value={}) as call:
            self.client.post('/rpc', json={"jsonrpc": "2.0", "method": "service.health", "params": {}})
            call.assert_called_once_with("service.health", {})

    def test_internal_failure_is_sanitized(self):
        with patch('MySolution.service.perform', side_effect=RuntimeError('secret C:\\private\\file')):
            with self.assertLogs('MySolution.rpc', level='ERROR'):
                result = self.error(self.call('lambda.typecheck', {'source': '1'}), -32603)
        self.assertEqual(result, {'code': -32603, 'message': 'Internal error'})

    def test_runtime_failure_not_timeout(self):
        self.error(self.call('lambda.interpret', {'source': '1 / 0'}), -32603)

    def test_timeout_http_and_process_cleanup(self):
        before = {p.pid for p in mp.active_children()}
        def timed_call(params, timeout):
            return run_interpretation(params, 0.3, worker_target=blocked_worker)
        with patch('MySolution.worker.run_interpretation', side_effect=timed_call):
            result = self.error(self.call('lambda.interpret', {'source': '1'}), -32012)
            self.assertEqual(result['data'], {'timeout_seconds': 0.3})
        self.assertEqual({p.pid for p in mp.active_children()}, before)
        self.success(self.call('service.health', {}))
        self.assertEqual(self.success(self.call('lambda.interpret', {'source': '2+3'}))['value'], '5')

    def test_real_backend_tiny_deadline(self):
        self.client = create_app(LanguageService(timeout_seconds=0.000001)).test_client()
        self.error(self.call('lambda.interpret', {'source': '1'}), -32012)


if __name__ == '__main__':
    unittest.main()
