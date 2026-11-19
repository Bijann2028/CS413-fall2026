"""Core solver, stream lifecycle, JSON-RPC, and HTTP contract tests."""
import json
import threading
import unittest
from urllib.request import Request, urlopen
from unittest.mock import patch

from MySolution import solver
from MySolution.rpc import RPCError, Service
from MySolution.server import make_server


def trace(size):
    stream = solver.open_stream(size)
    events = []
    while True:
        event, stream = solver.next_event(stream)
        events.append(event)
        if event['event'] == 'done':
            return events, stream


def reference(size):
    """Independent eager oracle used only for small test boards."""
    events = []
    def visit(board):
        row = len(board)
        if row == size:
            events.append(dict(event='solution', board=board))
            return
        for column in range(size):
            base = dict(column=column, row=row, board=board)
            events.append(dict(event='try', **base))
            if any(c == column or abs(c-column) == row-r for r, c in enumerate(board)):
                events.append(dict(event='reject', **base))
            else:
                events.append(dict(event='place', column=column, row=row, board=board+[column]))
                visit(board+[column])
                events.append(dict(event='backtrack', **base))
    visit([])
    events.append(dict(event='done'))
    return events


class SolverTests(unittest.TestCase):
    def test_cps_trace_and_safety(self):
        events, tail = trace(4)
        self.assertEqual(events, reference(4))
        self.assertEqual(solver.next_event(tail), (None, None))
        # Row 1 against row 0 column 0: same column and diagonal reject;
        # column 2 is safe. Both diagonal directions occur in the full trace.
        for col, kind in [(0, 'reject'), (1, 'reject'), (2, 'place')]:
            self.assertTrue(any(e['event'] == kind and e.get('row') == 1
                                and e.get('column') == col for e in events))

    def test_all_92_deterministic(self):
        events, _ = trace(8)
        boards = [tuple(e['board']) for e in events if e['event'] == 'solution']
        self.assertEqual(len(boards), 92)
        self.assertEqual(len(set(boards)), 92)
        self.assertEqual(boards, sorted(boards))
        self.assertEqual(boards[0], (0, 4, 7, 5, 2, 6, 1, 3))
        for board in boards:
            self.assertEqual(len(set(board)), 8)
            self.assertEqual(len({r-c for r,c in enumerate(board)}), 8)
            self.assertEqual(len({r+c for r,c in enumerate(board)}), 8)
        self.assertEqual(sum(e['event'] == 'done' for e in events), 1)
        self.assertEqual(events, trace(8)[0])

    def test_unforced_tails_large_boards(self):
        for size in (9, 10):
            stream = solver.open_stream(size)
            self.assertFalse(stream.evaluated)
            for _ in range(32):
                _, tail = solver.next_event(stream)
                self.assertTrue(stream.evaluated)
                self.assertFalse(tail.evaluated)
                stream = tail
            # Runtime counter and delayed-failure proofs are in test_review.py.

    def test_open_does_not_force_and_limit_is_exact(self):
        service = Service()
        with patch.object(solver, 'force', side_effect=AssertionError('forced')):
            sid = service.invoke('queens.open', {'size': 10})['stream_id']
        original = solver.next_event
        with patch.object(solver, 'next_event', wraps=original) as next_cell:
            result = service.invoke('queens.next', {'stream_id': sid, 'limit': 3})
            self.assertEqual(len(result['events']), 3)
            self.assertEqual(next_cell.call_count, 3)
        self.assertFalse(service.streams[sid]['stream'].evaluated)


class RPCTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.service = Service(clock=lambda: self.now)

    def call(self, method, params, rid='id'):
        return self.service.dispatch(dict(jsonrpc='2.0', id=rid, method=method, params=params))

    def test_lifecycle_and_independence(self):
        a = self.call('queens.open', {'size': 4})['result']['stream_id']
        b = self.call('queens.open', {'size': 4})['result']['stream_id']
        self.assertNotEqual(a, b)
        def advance(sid, n=1):
            return self.call('queens.next', dict(stream_id=sid, limit=n))['result']
        self.assertEqual(advance(a), advance(b))
        while not advance(a, 32)['done']:
            pass
        self.assertIsNone(self.service.streams[a]['stream'])
        self.assertEqual(advance(a), {'events': [], 'done': True})
        self.assertFalse(advance(b)['done'])
        self.assertEqual(self.call('queens.close', {'stream_id': a})['result'], {'closed': True})
        self.assertEqual(self.call('queens.next', dict(stream_id=a, limit=1))['error']['code'], -32001)
        self.now = 301
        self.assertEqual(self.call('queens.next', dict(stream_id=b, limit=1))['error']['code'], -32001)

    def test_validation_and_ids(self):
        self.assertEqual(self.call('service.health', {}, 0)['id'], 0)
        self.assertEqual(self.call('service.health', {}, None)['id'], None)
        for params in ({'size': True}, {'size': 3}, {'size': 11}, {'size': 8.0}, {'size': 8, 'source': 'bad'}):
            self.assertEqual(self.call('queens.open', params)['error']['code'], -32602)
        for limit in (0, 33, True, 1.5):
            self.assertEqual(self.call('queens.next', dict(stream_id='x', limit=limit))['error']['code'], -32602)
        self.assertEqual(self.call('bad', {})['error']['code'], -32601)
        self.assertEqual(self.service.dispatch([])['error']['code'], -32600)
        self.assertEqual(self.service.dispatch({'jsonrpc': '2.0', 'method': 7})['error']['code'], -32600)
        self.assertIsNone(self.service.dispatch({'jsonrpc': '2.0', 'method': 'bad'}))
        with patch.object(self.service, 'invoke', side_effect=RuntimeError('/private/path')):
            result = self.call('service.health', {})
        self.assertEqual(result['error'], {'code': -32603, 'message': 'Internal error'})

    def test_capacity(self):
        self.service.capacity = 1
        self.call('queens.open', {'size': 4})
        self.assertEqual(self.call('queens.open', {'size': 4})['error']['code'], -32002)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, body):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        with urlopen(Request(self.url+'/rpc', data, {'Content-Type': 'application/json'})) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def test_transport(self):
        status, body = self.post(dict(jsonrpc='2.0', id=41, method='service.health', params={}))
        self.assertEqual((status, body['id'], body['result']['status']), (200, 41, 'ok'))
        self.assertEqual(self.post(dict(jsonrpc='2.0', method='service.health')), (204, None))
        self.assertEqual(self.post('{bad')[1]['error']['code'], -32700)
        self.assertEqual(self.post([])[1]['error']['code'], -32600)
        for path in ('/', '/client.js', '/style.css'):
            with urlopen(self.url+path) as response:
                self.assertEqual(response.status, 200)

    def test_end_to_end_8(self):
        def call(method, params):
            return self.post(dict(jsonrpc='2.0', id=1, method=method, params=params))[1]['result']
        sid = call('queens.open', {'size': 8})['stream_id']
        boards = []
        while True:
            result = call('queens.next', dict(stream_id=sid, limit=32))
            boards.extend(tuple(e['board']) for e in result['events'] if e['event'] == 'solution')
            if result['done']:
                self.assertEqual(result['events'][-1], {'event': 'done'})
                break
        self.assertEqual(len(set(boards)), 92)
        self.assertEqual(len(boards), 92)
        self.assertEqual(call('queens.next', dict(stream_id=sid, limit=32)), {'events': [], 'done': True})


if __name__ == '__main__':
    unittest.main()
