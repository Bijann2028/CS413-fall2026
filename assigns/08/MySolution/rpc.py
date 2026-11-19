"""Small JSON-RPC dispatcher and bounded, process-local stream table."""
import threading
import time
import uuid
import math
from . import solver


class RPCError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message


class Service:
    def __init__(self, clock=time.monotonic, lifetime=300, capacity=128):
        self.clock, self.lifetime, self.capacity = clock, lifetime, capacity
        self.streams = {}
        self.lock = threading.Lock()

    def invoke(self, method, params):
        shapes = {'service.health': set(), 'queens.open': {'size'},
                  'queens.next': {'stream_id', 'limit'}, 'queens.close': {'stream_id'}}
        if method not in shapes:
            raise RPCError(-32601, 'Method not found')
        if not isinstance(params, dict) or set(params) != shapes[method]:
            raise RPCError(-32602, 'Invalid parameters')
        for key, low, high in [('size', 4, 10), ('limit', 1, 32)]:
            if key in params and (type(params[key]) is not int or not low <= params[key] <= high):
                raise RPCError(-32602, 'Invalid ' + key)
        if 'stream_id' in params and (not isinstance(params['stream_id'], str) or not params['stream_id']):
            raise RPCError(-32602, 'Invalid stream_id')
        with self.lock:
            now = self.clock()
            self.streams = {key: value for key, value in self.streams.items()
                            if now - value['touched'] < self.lifetime}
            if method == 'service.health':
                return {'status': 'ok', 'version': '1.0'}
            if method == 'queens.open':
                if len(self.streams) >= self.capacity:
                    raise RPCError(-32002, 'Stream capacity reached')
                sid = str(uuid.uuid4())
                self.streams[sid] = dict(stream=solver.open_stream(params['size']), touched=now)
                return {'stream_id': sid, 'size': params['size']}
            sid = params['stream_id']
            if sid not in self.streams:
                raise RPCError(-32001, 'Unknown, closed, or expired stream')
            if method == 'queens.close':
                del self.streams[sid]
                return {'closed': True}
            entry = self.streams[sid]
            events = []
            for _ in range(params['limit']):
                if entry['stream'] is None:
                    break
                event, tail = solver.next_event(entry['stream'])
                entry['stream'] = tail
                if event is None:
                    break
                events.append(event)
                if event['event'] == 'done':
                    entry['stream'] = None
                    break
            entry['touched'] = self.clock()
            return {'events': events, 'done': entry['stream'] is None}

    def dispatch(self, request):
        rid = request.get('id') if isinstance(request, dict) else None
        valid_id = (rid is None or type(rid) in (str, int)
                    or (type(rid) is float and math.isfinite(rid)))
        valid = (isinstance(request, dict) and request.get('jsonrpc') == '2.0'
                 and isinstance(request.get('method'), str)
                 and valid_id)
        if not valid:
            return error(None, -32600, 'Invalid Request')
        notification = 'id' not in request
        rid = request.get('id')
        try:
            result = self.invoke(request['method'], request.get('params', {}))
            response = {'jsonrpc': '2.0', 'id': rid, 'result': result}
        except RPCError as exc:
            response = error(rid, exc.code, exc.message)
        except Exception:
            response = error(rid, -32603, 'Internal error')
        return None if notification else response


def error(rid, code, message):
    return {'jsonrpc': '2.0', 'id': rid, 'error': {'code': code, 'message': message}}
