"""Executable checks for the submitted schemas, examples and demo verdicts."""
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator

from MySolution.app import create_app
from MySolution.demo import check_exchange

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'schema.json').read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        response_schema = {**cls.schema, 'oneOf': [{'$ref': '#/$defs/responsePayload'}]}
        cls.response_validator = Draft202012Validator(response_schema)

    def test_schema_is_valid_and_documented_examples_conform(self):
        contract = (ROOT / 'RPC.md').read_text(encoding='utf-8')
        examples = re.findall(r'```json\s*\n(.*?)\n```', contract, re.DOTALL)
        self.assertGreaterEqual(len(examples), 15)
        for example in examples:
            with self.subTest(example=example[:80]):
                self.validator.validate(json.loads(example))

    def test_schema_rejects_invalid_requests_and_responses(self):
        for request in ({'jsonrpc': '1.0', 'method': 'service.health'},
                        {'jsonrpc': '2.0', 'method': 1},
                        {'jsonrpc': '2.0', 'method': 'service.health', 'id': True}, []):
            self.assertFalse(self.validator.is_valid(request))
        for response in ({'jsonrpc': '2.0', 'id': 1},
                         {'jsonrpc': '2.0', 'id': 1, 'result': {}, 'error': {'code': -32603, 'message': 'Internal error'}},
                         {'jsonrpc': '2.0', 'id': 1, 'error': {'code': 'wrong', 'message': 'bad'}},
                         {'jsonrpc': '2.0', 'id': [], 'result': {}}):
            self.assertFalse(self.response_validator.is_valid(response))

    def test_saved_exchanges_match_live_service(self):
        client = create_app().test_client()
        paths = sorted((ROOT / 'examples').glob('*-exchange.json'))
        self.assertEqual(len(paths), 8)
        for path in paths:
            with self.subTest(path=path.name):
                record = json.loads(path.read_text(encoding='utf-8'))
                self.validator.validate(record['request'])
                self.response_validator.validate(record['response'])
                response = client.post('/rpc', json=record['request'])
                self.assertEqual(response.status_code, record['http_status'])
                self.assertEqual(response.get_json(), record['response'])

    def test_schema_accepts_real_mixed_batch_error_responses(self):
        payload = [{'jsonrpc': '2.0', 'method': 'service.health', 'params': {}, 'id': 0},
                   {'jsonrpc': '2.0', 'method': 'service.health', 'params': {}},
                   'invalid request']
        response = create_app().test_client().post('/rpc', json=payload)
        self.assertEqual(response.status_code, 200)
        self.response_validator.validate(response.get_json())

    def test_demo_rejects_unexpected_results_and_failures(self):
        request = {'jsonrpc': '2.0', 'method': 'lambda.interpret', 'params': {'source': '6*7'}, 'id': 2}
        for response in ({'jsonrpc': '2.0', 'id': 2, 'result': {'type': 'sint', 'value': '41'}},
                         {'jsonrpc': '2.0', 'id': 2, 'error': {'code': -32603, 'message': 'Internal error'}}):
            with self.assertRaises(AssertionError):
                check_exchange({'request': request, 'http_status': 200, 'response': response},
                               {'type': 'sint', 'value': '42'})
