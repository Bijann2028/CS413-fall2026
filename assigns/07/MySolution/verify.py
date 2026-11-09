"""Run both suites, starting and cleaning up a real HTTP server automatically."""
import os
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen


def main():
    assignment = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                    'MySolution/tests', '-v'], cwd=assignment, check=True)
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    url = f'http://127.0.0.1:{port}/rpc'
    command = [sys.executable, '-B', '-m', 'flask', '--app',
               'MySolution.app:create_app', 'run', '--host', '127.0.0.1', '--port', str(port)]
    with tempfile.TemporaryFile(mode='w+t', encoding='utf-8') as log:
        server = subprocess.Popen(command, cwd=assignment, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            while True:
                if server.poll() is not None:
                    raise RuntimeError('Verification server exited before startup')
                if time.monotonic() >= deadline:
                    raise RuntimeError('Verification server startup timed out')
                try:
                    req = Request(url, data=b'{"jsonrpc":"2.0","method":"service.health","params":{},"id":1}',
                                  headers={'Content-Type': 'application/json'})
                    with urlopen(req, timeout=0.5) as response:
                        body = json.load(response)
                        if body == {'jsonrpc': '2.0', 'id': 1,
                                    'result': {'status': 'ok', 'version': '1.0'}}:
                            break
                except OSError:
                    time.sleep(0.05)
            env = dict(os.environ, LAMBDA_RPC_URL=url)
            subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'TEST', '-v'],
                           cwd=assignment, env=env, check=True)
        except Exception:
            log.seek(0)
            print(log.read()[-4000:], file=sys.stderr)
            raise
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    main()
