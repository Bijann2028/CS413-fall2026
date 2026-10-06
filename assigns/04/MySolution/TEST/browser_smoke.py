"""Real browser acceptance checks; real language tools except explicit fault injection."""
import argparse
import json
from pathlib import Path
import platform
import re
import sys
from threading import Event, Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app
from backend import LambdaBackend
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server, WSGIRequestHandler


class QuietHandler(WSGIRequestHandler):
    def log(self, *args, **kwargs):
        pass


def smoke(channel="msedge", report=None):
    app = create_app()
    controller = app.extensions["controller"]
    real_backend = controller.backend
    server = make_server("127.0.0.1", 0, app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    checks = []
    release = Event()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=channel, headless=True)
            browser_version = browser.version
            page = browser.new_page(viewport={"width": 1100, "height": 1000})
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            menu, editor = page.locator("#source-menu"), page.locator("#editor")
            apply, discard = page.get_by_role("button", name="Apply changes"), page.get_by_role("button", name="Discard changes")
            execute = page.get_by_role("button", name="Execute", exact=True)
            lint = page.get_by_role("button", name="Lint", exact=True)
            interpret = page.get_by_role("button", name="Interpret", exact=True)

            def record(check, requirements, observed):
                checks.append({"check": check, "requirements": requirements, "observed": observed, "outcome": "passed"})
                print(f"{check}: PASS - {observed}", flush=True)

            def apply_source(source):
                editor.fill(source)
                expect(apply).to_be_enabled()
                apply.click()
                expect(lint).to_be_enabled()

            def run(button, outcome, text):
                before = page.locator(".result").count()
                button.click()
                expect(page.locator(".result")).to_have_count(before + 1, timeout=10000)
                result = page.locator(".result").last
                expect(result.locator("h3")).to_contain_text(outcome)
                expect(result.locator("pre")).to_contain_text(text)
                expect(lint).to_be_enabled()

            expect(menu).to_be_enabled()
            expect(lint).to_be_disabled()
            expect(execute).to_be_disabled()
            assert page.locator("#actions button").all_text_contents() == ["Lint", "Interpret", "Type-check", "Compile", "Execute"]
            assert menu.locator("option").all_text_contents()[1:] == ["Choose File", "Manual input", "Factorial (canned)", "Fibonacci (canned)"]
            menu.select_option("manual")
            expect(editor).to_have_value("")
            apply_source('D0Eop2("+", D0Eint(20), D0Eint(22))')
            expect(page.locator("#source-info")).to_contain_text("revision 1")
            run(interpret, "success", "D0Vint(arg1=42)")
            record("B1", ["F1", "F2", "F4", "F6", "F9"], "Manual input without upload; arithmetic returned 42; controls in required order.")

            editor.fill("D0Eint(43)")
            expect(menu).to_be_disabled()
            expect(lint).to_be_disabled()
            expect(discard).to_be_enabled()
            discard.click()
            expect(editor).to_have_value('D0Eop2("+", D0Eint(20), D0Eint(22))')
            apply_source("D0Eint(43)")
            expect(page.locator("#source-info")).to_contain_text("revision 2")
            expect(page.locator(".result")).to_have_count(0)
            record("B2", ["F2", "F8"], "Dirty edits blocked tools and source replacement; Discard restored source; Apply increased revision and cleared results.")

            for example, output in [("factorial", "120"), ("fibonacci", "55")]:
                menu.select_option(example)
                expect(editor).to_have_value(re.compile("D0Efix"))
                run(lint, "success", "No free variables")
                run(interpret, "success", f"D0Vint(arg1={output})")
            record("B3", ["F1", "F5", "F6", "F8"], "Editable factorial and Fibonacci examples linted successfully and returned 120 and 55.")

            apply_source('D0Evar("x")')
            run(lint, "language_error", "Undeclared variables: x")
            apply_source("D0Eint(1)")
            run(lint, "success", "No free variables")
            apply_source('D0Eop2("/", D0Eint(1), D0Eint(0))')
            run(lint, "success", "No free variables")
            run(interpret, "runtime_error", "ZeroDivisionError")
            apply_source('D0Eint("wrong")')
            run(interpret, "input_error", "must be int")
            record("B4", ["F5", "F6"], "Open expression listed x; closed edit passed; division by zero passed Lint but failed Interpret; bad argument reported input_error.")

            run(page.get_by_role("button", name="Type-check", exact=True), "not_implemented", "Type checking is not yet implemented")
            run(page.get_by_role("button", name="Compile", exact=True), "not_implemented", "Compilation is not yet implemented")
            expect(execute).to_be_disabled()
            expect(page.locator("#execute-help")).to_contain_text("generated code")
            record("B5", ["F4", "F7"], "Both placeholders reported not_implemented; Execute stayed disabled with an explanation.")

            old_info = page.locator("#source-info").inner_text()
            old_results = page.locator(".result").count()
            editor.fill(" \n ")
            expect(apply).to_be_enabled()
            apply.click()
            expect(page.locator("#error")).to_contain_text("empty")
            expect(editor).to_have_value(" \n ")
            expect(page.locator("#source-info")).to_have_text(old_info)
            expect(page.locator(".result")).to_have_count(old_results)
            discard.click()
            expect(menu).to_be_enabled()
            menu.select_option("file")
            source_file = page.locator("#source-file")
            upload = page.get_by_role("button", name="Load selected file")
            source_file.set_input_files({"name": "bad.lambda", "mimeType": "text/plain", "buffer": b"\xff"})
            upload.click()
            expect(page.locator("#error")).to_contain_text("UTF-8")
            expect(page.locator("#source-info")).to_have_text(old_info)
            source_file.set_input_files({"name": "large.lambda", "mimeType": "text/plain", "buffer": b"x" * 65537})
            upload.click()
            expect(page.locator("#error")).to_contain_text("65,536")
            expect(page.locator("#source-info")).to_have_text(old_info)
            source_file.set_input_files({"name": "open.lambda", "mimeType": "text/plain", "buffer": b'D0Evar("x")\r\n'})
            upload.click()
            expect(editor).to_have_value('D0Evar("x")\n')
            expect(page.locator("#source-info")).to_contain_text("open.lambda")
            run(lint, "language_error", "Undeclared variables: x")
            record("B6", ["F1", "F3", "F8"], "Blank edits stayed available; invalid UTF-8 and oversized uploads preserved state; a Windows CRLF upload replaced source and allowed Lint.")

            literal = '<img src=x onerror="window.injected=true">'
            source = "# first line\nD0Evar(" + repr(literal) + ")\n"
            apply_source(source)
            run(lint, "language_error", literal)
            expect(editor).to_have_value(source)
            assert page.locator("#results img").count() == 0
            assert page.evaluate("window.injected === undefined")
            expect(page.locator(".result").last.locator("h3")).to_contain_text("revision")
            record("B7", ["F9"], "Multiline source and HTML-like diagnostic stayed literal; no image element or injected script appeared.")

            apply_source("D0Eint(42)")
            entered = Event()

            class FaultBackend:
                def lint(self, source, revision):
                    entered.set()
                    if not release.wait(5):
                        raise RuntimeError("test timeout")
                    raise RuntimeError("injected outage")

            controller.backend = FaultBackend()
            lint.click()
            assert entered.wait(2)
            expect(page.locator("#status")).to_contain_text("Busy: Lint")
            expect(menu).to_be_disabled()
            expect(interpret).to_be_disabled()
            expect(editor).to_have_attribute("readonly", "")
            expect(discard).to_be_disabled()
            release.set()
            expect(page.locator(".result").last.locator("h3")).to_contain_text("backend_error")
            expect(lint).to_be_enabled()
            expect(editor).to_have_value("D0Eint(42)")
            controller.backend = real_backend
            run(lint, "success", "No free variables")
            record("B8", ["F10"], "Injected outage exposed busy state and blocked conflicts, preserved source, restored controls, and allowed real Lint retry.")

            controller.backend = LambdaBackend(timeout=0.001)
            run(interpret, "timeout", "worker terminated")
            controller.backend = real_backend
            run(interpret, "success", "D0Vint(arg1=42)")
            record("B9", ["F6", "F10"], "A real worker timeout preserved source; retry of the same source returned 42.")

            # A keyboard-only edit/apply/lint path using labeled focusable controls.
            editor.focus()
            page.keyboard.press("ControlOrMeta+A")
            page.keyboard.type("D0Eint(7)")
            expect(apply).to_be_enabled()
            page.keyboard.press("Tab")
            expect(apply).to_be_focused()
            page.keyboard.press("Enter")
            expect(lint).to_be_enabled()
            page.keyboard.press("Tab")  # skips the now-disabled Discard button
            expect(lint).to_be_focused()
            page.keyboard.press("Enter")
            expect(page.locator(".result").last.locator("pre")).to_contain_text("No free variables")
            record("B10", ["F2", "F4", "F5"], "Keyboard-only typing, Tab navigation, Apply, and Lint worked; statuses used text labels.")
            (ROOT / "test-results").mkdir(exist_ok=True)
            page.screenshot(path=str(ROOT / "test-results" / "workspace.png"), full_page=True)
            browser.close()
        result = {"python": platform.python_version(), "platform": platform.platform(),
                  "browser_channel": channel, "browser_version": browser_version, "checks": checks}
        if report:
            Path(report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in result.items() if key != "checks"}))
        return result
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="msedge", help="Installed Playwright browser channel: msedge or chrome")
    parser.add_argument("--report", help="Optional JSON report path")
    args = parser.parse_args()
    smoke(args.channel, args.report)
