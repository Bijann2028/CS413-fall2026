"""Real-browser acceptance checks against the actual HTTP/LAMBDA3 service.

From assigns/08: python -B -m MySolution.tests.browser_check
Only explicit outage/pause checks inject faults; all search events are real.
"""
import argparse
import json
import platform
import re
from threading import Event, Thread

from playwright.sync_api import expect, sync_playwright
from MySolution.rpc import Service
from MySolution.server import make_server


class ObservableService(Service):
    def __init__(self):
        super().__init__()
        self.hold_next = False
        self.entered = Event()
        self.release = Event()
        self.next_calls = 0

    def invoke(self, method, params):
        if method == 'queens.next':
            self.next_calls += 1
            if self.hold_next:
                self.entered.set()
                if not self.release.wait(10):
                    raise RuntimeError('Browser test did not release request')
        return super().invoke(method, params)


def run(channel):
    service = ObservableService()
    server = make_server(port=0, service=service)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    checks = []
    page_errors = []
    rpc_requests = []

    def record(name, requirements, observed):
        checks.append(dict(check=name, requirements=requirements, observed=observed, outcome='passed'))
        print(f'{name}: PASS — {observed}', flush=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=channel, headless=True)
            version = browser.version
            page = browser.new_page(viewport={'width': 1200, 'height': 950})
            page.on('pageerror', lambda error: page_errors.append(str(error)))
            page.on('request', lambda request: rpc_requests.append(request.post_data_json)
                    if request.url.endswith('/rpc') else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            expect(page.locator('#board .cell')).to_have_count(64)
            expect(page.locator('#size')).to_have_value('8')
            assert rpc_requests == []
            # Keyboard-only start and step; focus indicator must be visible.
            page.locator('#start').focus()
            assert page.locator('#start').evaluate("e => getComputedStyle(e).outlineStyle !== 'none'")
            page.keyboard.press('Enter')
            expect(page.locator('#status')).to_contain_text('Stream opened')
            assert service.next_calls == 0
            page.locator('#step').focus()
            page.keyboard.press('Space')
            expect(page.locator('#status')).to_contain_text('try — row 0, column 0')
            assert service.next_calls == 1
            expect(page.locator('#board .try')).to_have_count(1)
            expect(page.locator('#board')).to_have_attribute('aria-label', re.compile('try.*row 0'))
            record('B1', ['start', 'step', 'incremental', 'keyboard', 'color independence'],
                   'Default 8×8; keyboard Start fetched no events; keyboard Step fetched one candidate with textual coordinates.')

            page.locator('#size').select_option('4')
            page.locator('#start').click()
            expect(page.locator('#board .cell')).to_have_count(16)
            for kind in ('try', 'place', 'try', 'reject'):
                page.locator('#step').click()
                expect(page.locator('#status')).to_contain_text(kind)
            expect(page.locator('#status')).to_contain_text('same column conflict with row 0')
            expect(page.locator('#board .reject')).to_have_count(1)
            assert page.locator('#board .cell').evaluate_all("cells => cells.filter(e=>e.textContent==='♛').length") == 2
            record('B2', ['try', 'place', 'reject', 'board snapshots', 'color independence'],
                   'Safe queen persisted; rejected candidate was distinct and its same-column conflict was explained in text.')

            # Pause while a real server request is held before consumption.
            service.hold_next = True
            before = service.next_calls
            page.locator('#play').focus()
            page.keyboard.press('Enter')
            assert service.entered.wait(3)
            expect(page.locator('#reset')).to_be_disabled()
            page.get_by_role('button', name='Pause', exact=True).focus()
            page.keyboard.press('Space')
            service.hold_next = False
            service.release.set()
            expect(page.locator('#reset')).to_be_enabled()
            page.wait_for_timeout(350)
            assert service.next_calls == before + 1
            expect(page.locator('#play')).to_have_text('Play')
            record('B3', ['play/pause', 'one outstanding request'],
                   'Pause remained usable during a held HTTP call; exactly that call finished, with no subsequent event fetched.')

            page.locator('#speed').fill('0')
            page.locator('#next').focus()
            page.keyboard.press('Enter')
            expect(page.locator('#count')).to_have_text('1', timeout=15000)
            expect(page.locator('#play')).to_have_text('Play')
            expect(page.locator('#board')).to_have_class('solution')
            assert page.locator('#board .cell').evaluate_all("cells => cells.filter(e=>e.textContent==='♛').length") == 4
            n = service.next_calls
            page.wait_for_timeout(120)
            assert service.next_calls == n
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            record('B4', ['next solution', 'solution counter', 'responsive layout'],
                   'Next solution paused on the first real 4×4 solution; all four queens rendered; mobile layout had no horizontal overflow.')

            page.locator('#step').click()
            expect(page.locator('#status')).to_contain_text('backtrack')
            expect(page.locator('#board .backtrack')).to_have_count(1)
            assert page.locator('#board .cell').evaluate_all("cells => cells.filter(e=>e.textContent==='♛').length") == 3
            page.locator('#play').click()
            expect(page.locator('#status')).to_contain_text('Search complete. 2 solutions.', timeout=15000)
            expect(page.locator('#count')).to_have_text('2')
            n = service.next_calls
            page.locator('#step').click()
            page.wait_for_timeout(100)
            assert service.next_calls == n
            page.locator('#reset').focus()
            page.keyboard.press('Enter')
            expect(page.locator('#count')).to_have_text('0')
            expect(page.locator('#status')).to_contain_text('Ready')
            assert not service.streams
            record('B5', ['backtrack', 'play', 'completion', 'reset', 'cleanup'],
                   'Backtrack restored three queens; Play reached exactly two solutions and done; Step after completion fetched nothing; Reset removed server state.')

            def outage(route):
                route.fulfill(status=200, content_type='application/json',
                              body=json.dumps({'jsonrpc': '2.0', 'id': 1,
                                               'error': {'code': -32603, 'message': 'Injected outage'}}))
            page.route('**/rpc', outage)
            page.locator('#start').click()
            expect(page.locator('#status')).to_contain_text('Error: Injected outage')
            expect(page.locator('#start')).to_be_enabled()
            page.unroute('**/rpc', outage)
            page.locator('#start').click()
            expect(page.locator('#status')).to_contain_text('Stream opened')
            def offline(route):
                route.abort('failed')
            page.route('**/rpc', offline)
            page.locator('#step').click()
            expect(page.locator('#status')).to_contain_text('Error:')
            expect(page.locator('#start')).to_be_enabled()
            page.unroute('**/rpc', offline)
            # Simulate expiry, then verify Start can recover from failed close.
            service.streams.clear()
            page.locator('#start').click()
            expect(page.locator('#status')).to_contain_text('Stream opened')
            assert len(service.streams) == 1
            record('B6', ['RPC failure', 'network failure', 'restart', 'expired ID'],
                   'Injected RPC and network failures were visible; controls recovered; Start reopened after an expired stream ID.')

            assert all(request['params']['limit'] == 1 for request in rpc_requests if request['method'] == 'queens.next')
            assert not page_errors, page_errors
            browser.close()
            report = dict(python=platform.python_version(), browser=f'{channel} {version}',
                          checks=checks, page_errors=page_errors,
                          next_requests=sum(r['method'] == 'queens.next' for r in rpc_requests))
            print(json.dumps(report, indent=2, ensure_ascii=False))
    finally:
        service.release.set()
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', default='msedge')
    args = parser.parse_args()
    run(args.channel)
