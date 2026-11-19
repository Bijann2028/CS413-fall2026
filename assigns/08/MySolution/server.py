"""Local HTTP transport; no third-party dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from .rpc import Service, error

STATIC = Path(__file__).parent / 'static'


def make_server(host='127.0.0.1', port=8000, service=None):
    service = service or Service()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body=b'', content_type='application/json'):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            files = {'/': ('index.html', 'text/html; charset=utf-8'),
                     '/client.js': ('client.js', 'text/javascript; charset=utf-8'),
                     '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if self.path not in files:
                return self.reply(404)
            name, kind = files[self.path]
            self.reply(200, (STATIC / name).read_bytes(), kind)

        def do_POST(self):
            if self.path != '/rpc':
                return self.reply(404)
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                return self.reply(415)
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= 65536:
                    return self.reply(413)
                request = json.loads(self.rfile.read(size), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                response = service.dispatch(request)
            except (ValueError, UnicodeDecodeError, RecursionError):
                response = error(None, -32700, 'Parse error')
            if response is None:
                self.reply(204)
            else:
                self.reply(200, json.dumps(response, allow_nan=False).encode('utf-8'))

    return ThreadingHTTPServer((host, port), Handler)


def main():
    with make_server() as server:
        print('Assignment 8: http://127.0.0.1:8000', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
