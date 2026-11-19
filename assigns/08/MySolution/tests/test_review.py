"""Independent checks added after comparing assignments 1–6 feedback."""
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import math
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from MySolution import solver
from MySolution.rpc import Service
import test_core
from test_core import reference, trace


class SolverReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Expose the SAME checked helpers, rather than reimplementing safety.
        source = (solver.HERE / 'queens.lam').read_text(encoding='utf-8')
        expression, _ = solver.L.d0exp_parse_and_typecheck(
            source.replace('in solve end', 'in (solve, safe, emit) end'))
        namespace = {}
        exec(solver.L.d0exp_compile(expression), namespace)
        cls.helpers = namespace['_lambda_result']
        cls.helper_runtime = namespace

    def test_cps_safety_calls_only_correct_continuation(self):
        safe = self.helpers[1]
        for column, board, expected in [(2, [2], 'conflict'), (1, [2], 'conflict'),
                                        (3, [2], 'conflict'), (0, [2], 'safe'),
                                        (3, [], 'safe'), (0, [3, 0], 'conflict')]:
            with self.subTest(column=column, board=board):
                called = []
                def yes(_):
                    called.append('safe')
                    return 'safe'
                def no(_):
                    called.append('conflict')
                    return 'conflict'
                self.assertEqual(safe((column, 1, board, yes, no)), expected)
                self.assertEqual(called, [expected])

    def test_emit_does_not_run_delayed_failure_until_tail_forced(self):
        emit = self.helpers[2]
        calls = []
        def fail(_):
            calls.append('tail')
            raise RuntimeError('deliberately delayed')
        cell = emit(((0, 0, 0, []), fail))
        self.assertEqual(calls, [])
        first = self.helper_runtime['_lambda_lazy_eval'](cell)
        self.assertEqual(first['head'], (0, 0, 0, []))
        self.assertEqual(calls, [])
        with self.assertRaisesRegex(RuntimeError, 'deliberately delayed'):
            self.helper_runtime['_lambda_lazy_eval'](first['tail'])
        self.assertEqual(calls, ['tail'])

    def test_lazy_thunk_counters_and_memoization(self):
        original = solver.runtime['_lambda_lazy_make']
        forced = []
        def tracked(thunk):
            def run(unit):
                forced.append(thunk)
                return thunk(unit)
            return original(run)
        with patch.dict(solver.runtime, {'_lambda_lazy_make': tracked}):
            for size in (4, 8, 9, 10):
                with self.subTest(size=size):
                    forced.clear()
                    stream = solver.open_stream(size)
                    self.assertEqual(forced, [])
                    for _ in range(32):
                        node = solver.force(stream)
                        n = len(forced)
                        self.assertIs(solver.force(stream), node)
                        self.assertEqual(len(forced), n)
                        self.assertFalse(node['tail'].evaluated)
                        stream = node['tail']
                    self.assertGreater(len(forced), 0)

    def test_interpreter_and_compiler_agree_on_complete_four_trace(self):
        L = solver.L
        factory = L.d0exp_evaluate(solver.expression)
        stream = L._d0val_apply(factory, L.D0Vint(4))
        result = []
        while True:
            node = L.d0exp_evaluate(L.D0Eop1('lazy_eval', L.D0Evar('stream')),
                                    L.ENVcns('stream', stream, L.ENVnil()))
            if not node.is_cons:
                break
            kind, column, row, board = node.head.arg1
            columns = []
            items = board.arg1
            while isinstance(items, L.fnlist_cons):
                columns.append(items.arg1.arg1)
                items = items.arg2
            event = {'event': solver.KINDS[kind.arg1]}
            if kind.arg1 != 5:
                event['board'] = columns[::-1]
            if kind.arg1 < 4:
                event.update(column=column.arg1, row=row.arg1)
            result.append(event)
            stream = node.tail
        self.assertEqual(result, reference(4))
        self.assertEqual(result, trace(4)[0])

    def test_all_sizes_known_solution_counts(self):
        for size, count in [(4, 2), (5, 10), (6, 4), (7, 40), (8, 92), (9, 352), (10, 724)]:
            with self.subTest(size=size):
                stream = solver.open_stream(size)
                boards = set()
                solutions = 0
                while True:
                    event, stream = solver.next_event(stream)
                    if event['event'] == 'solution':
                        board = tuple(event['board'])
                        self.assertEqual(len(board), size)
                        boards.add(board)
                        solutions += 1
                    if event['event'] == 'done':
                        break
                self.assertEqual((solutions, len(boards)), (count, count))

    def test_eight_boards_match_independent_permutation_oracle(self):
        expected = [board for board in itertools.permutations(range(8))
                    if len({r-c for r, c in enumerate(board)}) == 8
                    and len({r+c for r, c in enumerate(board)}) == 8]
        events, _ = trace(8)
        self.assertEqual([tuple(e['board']) for e in events if e['event'] == 'solution'], expected)
        self.assertEqual(events, reference(8))


class RPCReviewTests(unittest.TestCase):
    def test_nonfinite_ids_rejected(self):
        service = Service()
        for rid in (math.inf, -math.inf, math.nan):
            response = service.dispatch(dict(jsonrpc='2.0', id=rid, method='service.health'))
            self.assertEqual(response['error']['code'], -32600)
            self.assertIsNone(response['id'])
            json.dumps(response, allow_nan=False)

    def test_exact_limits_and_final_short_batch(self):
        for limit in (1, 32):
            service = Service()
            sid = service.invoke('queens.open', {'size': 4})['stream_id']
            received = []
            while True:
                result = service.invoke('queens.next', dict(stream_id=sid, limit=limit))
                self.assertLessEqual(len(result['events']), limit)
                received.extend(result['events'])
                if result['done']:
                    break
                self.assertEqual(len(result['events']), limit)
            self.assertEqual(received, reference(4))
            self.assertEqual(service.invoke('queens.next', dict(stream_id=sid, limit=limit)),
                             {'events': [], 'done': True})

    def test_notifications_apply_state_without_response(self):
        service = Service()
        self.assertIsNone(service.dispatch(dict(jsonrpc='2.0', method='queens.open', params={'size': 4})))
        sid = next(iter(service.streams))
        self.assertIsNone(service.dispatch(dict(jsonrpc='2.0', method='queens.next', params=dict(stream_id=sid, limit=1))))
        result = service.invoke('queens.next', dict(stream_id=sid, limit=1))
        self.assertEqual(result['events'][0]['event'], 'place')
        self.assertIsNone(service.dispatch(dict(jsonrpc='2.0', method='queens.close', params={'stream_id': sid})))
        self.assertEqual(service.streams, {})

    def test_expiry_boundary_refresh_and_capacity_recovery(self):
        now = [0]
        service = Service(clock=lambda: now[0], lifetime=300, capacity=1)
        sid = service.invoke('queens.open', {'size': 4})['stream_id']
        now[0] = 299
        service.invoke('queens.next', dict(stream_id=sid, limit=1))
        now[0] = 598
        service.invoke('service.health', {})
        self.assertIn(sid, service.streams)
        now[0] = 599
        other = service.invoke('queens.open', {'size': 4})['stream_id']
        self.assertNotIn(sid, service.streams)
        self.assertIn(other, service.streams)

    def test_malformed_envelopes_and_parameter_shapes(self):
        service = Service()
        for request in (None, False, 3, 'request', [], {},
                        {'jsonrpc': '1.0', 'id': 1, 'method': 'service.health'},
                        {'jsonrpc': '2.0', 'id': True, 'method': 'service.health'},
                        {'jsonrpc': '2.0', 'id': [], 'method': 'service.health'},
                        {'jsonrpc': '2.0', 'method': 3}):
            with self.subTest(request=request):
                self.assertEqual(service.dispatch(request)['error']['code'], -32600)
        for method in ('service.health', 'queens.open', 'queens.next', 'queens.close'):
            for params in (None, [], 8, 'params'):
                request = dict(jsonrpc='2.0', id='same', method=method, params=params)
                response = service.dispatch(request)
                self.assertEqual(response['error']['code'], -32602)
                self.assertEqual(response['id'], 'same')
        self.assertEqual(service.streams, {})

    def test_valid_ids_preserved(self):
        for rid in (None, 0, -1, 1.25, 10**100, '', 'request-π'):
            response = Service().dispatch(dict(jsonrpc='2.0', id=rid, method='service.health'))
            self.assertEqual(response['id'], rid)
            self.assertIn('result', response)

    def test_concurrent_requests_cannot_duplicate_or_skip_events(self):
        service = Service()
        sid = service.invoke('queens.open', {'size': 4})['stream_id']
        with ThreadPoolExecutor(max_workers=8) as pool:
            batches = list(pool.map(lambda _: service.invoke('queens.next', dict(stream_id=sid, limit=1)), range(80)))
        # Thread completion order is unspecified; the multiset must be exact.
        actual = sorted(json.dumps(result['events'][0], sort_keys=True) for result in batches)
        expected = sorted(json.dumps(event, sort_keys=True) for event in reference(4)[:80])
        self.assertEqual(actual, expected)


class HTTPReviewTests(unittest.TestCase):
    # Reuses only the fixture; existing tests are not counted twice.
    setUpClass = classmethod(test_core.HTTPTests.setUpClass.__func__)
    tearDownClass = classmethod(test_core.HTTPTests.tearDownClass.__func__)
    post = test_core.HTTPTests.post
    def test_exponent_overflow_id_is_json_error_response(self):
        status, body = self.post('{"jsonrpc":"2.0","id":1e400,"method":"service.health"}')
        self.assertEqual(status, 200)
        self.assertEqual(body['error']['code'], -32600)

    def test_parser_recursion_failure_does_not_disconnect(self):
        # Fault injection exercises platform-dependent parser depth limits.
        with patch('MySolution.server.json.loads', side_effect=RecursionError()):
            from urllib.request import Request, urlopen
            with urlopen(Request(self.url+'/rpc', b'[]', {'Content-Type': 'application/json'})) as response:
                status, raw = response.status, response.read()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['error']['code'], -32700)

    def test_http_rejections_and_invalid_json(self):
        for path, body, content_type, status in (
                ('/other', b'{}', 'application/json', 404),
                ('/rpc', b'{}', 'text/plain', 415),
                ('/rpc', b'x' * 65537, 'application/json', 413)):
            with self.subTest(status=status):
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(self.url+path, body, {'Content-Type': content_type}))
                self.assertEqual(caught.exception.code, status)
        for raw in (b'', b'\xff', b'{"x":NaN}', b'{"x":Infinity}'):
            with urlopen(Request(self.url+'/rpc', raw, {'Content-Type': 'application/json'})) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response)['error']['code'], -32700)
