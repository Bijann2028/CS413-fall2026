import io
from pathlib import Path
import sys
from threading import Event
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app
from backend import LambdaBackend
from contracts import Artifact, MAX_SOURCE_BYTES, Result
from controller import Controller
from model import Model, StateError


def wait(controller):
    deadline = time.monotonic() + 5
    while controller.state()["busy"]:
        if time.monotonic() > deadline:
            raise AssertionError("Controller remained busy")
        time.sleep(0.01)
    return controller.state()


class ModelTests(unittest.TestCase):
    # These tests construct the model directly; no browser, HTTP request, or server.
    def test_manual_edit_apply_discard_and_revision(self):
        model = Model()
        model.edit("D0Eint(42)")
        model.apply()
        self.assertEqual((model.source, model.revision, model.name), ("D0Eint(42)", 1, "Manual input"))
        model.edit("D0Eint(43)")
        for action in [lambda: model.begin("lint"), lambda: model.replace("D0Eint(1)", "Other")]:
            with self.assertRaises(StateError):
                action()
        model.discard()
        self.assertEqual(model.draft, "D0Eint(42)")
        self.assertEqual(model.revision, 1)
        model.manual()
        self.assertEqual(model.draft, "")
        self.assertEqual(model.source, "D0Eint(42)")
        self.assertTrue(model.dirty)
        model.discard()
        self.assertFalse(model.dirty)
        model.edit("D0Eint(43)")
        model.apply()
        self.assertEqual(model.revision, 2)

    def test_rejected_changes_preserve_applied_state_and_rejected_draft(self):
        model = Model()
        model.replace("D0Eint(1)", "Original")
        model.begin("lint")
        result = Result("lint", 1, "success", "Passed")
        model.finish(result)
        for invalid in ["", "  \n", "é" * (MAX_SOURCE_BYTES // 2 + 1)]:
            model.edit(invalid)
            with self.assertRaises(StateError):
                model.apply()
            self.assertEqual((model.source, model.name, model.revision), ("D0Eint(1)", "Original", 1))
            self.assertEqual(model.draft, invalid)
            self.assertEqual(model.results, [result])
            model.discard()
        with self.assertRaises(StateError):
            model.replace("", "Bad upload")
        self.assertEqual(model.source, "D0Eint(1)")

    def test_accepted_changes_clear_results_and_artifacts(self):
        model = Model()
        model.replace("D0Eint(1)", "First")
        model.begin("compile")
        artifact = Artifact(1, "future-target", b"compiled bytes")
        model.finish(Result("compile", 1, "success", "Compiled", artifact=artifact))
        self.assertIs(model.artifact, artifact)
        model.replace("D0Eint(2)", "Second")
        self.assertEqual(model.revision, 2)
        self.assertEqual(model.results, [])
        self.assertIsNone(model.artifact)

    def test_failed_recompilation_and_stale_artifact(self):
        model = Model()
        model.replace("D0Eint(1)", "Source")
        model.artifact = Artifact(1, "future", b"code")
        model.begin("compile")
        self.assertIsNone(model.artifact)
        model.finish(Result("compile", 1, "not_implemented", "Unavailable"))
        with self.assertRaises(StateError):
            model.begin("execute")
        model.artifact = Artifact(0, "future", b"stale")
        with self.assertRaises(StateError):
            model.begin("execute")

    def test_no_source_busy_and_result_contract(self):
        model = Model()
        with self.assertRaises(StateError):
            model.begin("lint")
        model.replace("D0Eint(1)", "Source")
        with self.assertRaises(StateError):
            model.begin("unknown")
        model.begin("interpret")
        for action in [lambda: model.edit("new"), model.apply, model.discard, model.manual,
                       lambda: model.replace("D0Eint(2)", "Other"), lambda: model.begin("lint")]:
            with self.assertRaises(StateError):
                action()
        with self.assertRaises(StateError):
            model.finish(Result("interpret", 0, "success", "Wrong revision"))
        model.finish(Result("interpret", 1, "runtime_error", "Failure"))
        self.assertIsNone(model.busy)
        self.assertEqual(model.source, "D0Eint(1)")


class RecordingBackend:
    def __init__(self):
        self.calls = []

    def __getattr__(self, operation):
        def run(source, revision):
            self.calls.append((operation, source, revision))
            return Result(operation, revision, "not_implemented" if operation in ("compile", "typecheck") else "success", "Test response")
        return run


class ControllerTests(unittest.TestCase):
    def test_substitute_backend_dispatch_without_view_changes(self):
        backend = RecordingBackend()
        controller = Controller(Model(), backend)
        controller.change("apply", draft="D0Eint(1)")
        for operation in ("lint", "interpret", "typecheck", "compile"):
            controller.start(operation)
            state = wait(controller)
            self.assertEqual(state["results"][-1]["operation"], operation)
        self.assertEqual([call[0] for call in backend.calls], ["lint", "interpret", "typecheck", "compile"])
        self.assertTrue(all(call[1:] == ("D0Eint(1)", 1) for call in backend.calls))
        self.assertEqual(state["results"][-1]["outcome"], "not_implemented")
        with self.assertRaises(StateError):
            controller.start("execute")
        self.assertFalse(state["has_artifact"])

    def test_busy_failure_and_successful_retry(self):
        entered, release = Event(), Event()

        class FailingBackend:
            def lint(self, source, revision):
                entered.set()
                if not release.wait(3):
                    raise RuntimeError("test wait expired")
                raise RuntimeError("injected backend outage")

        controller = Controller(Model(), FailingBackend())
        controller.change("apply", draft="D0Eint(42)")
        controller.start("lint")
        self.assertTrue(entered.wait(1))
        self.assertEqual(controller.state()["busy"], "lint")
        try:
            with self.assertRaises(StateError):
                controller.change("discard")
            with self.assertRaises(StateError):
                controller.start("interpret")
        finally:
            release.set()
        state = wait(controller)
        self.assertEqual(state["results"][-1]["outcome"], "backend_error")
        self.assertEqual(state["source"], "D0Eint(42)")
        controller.backend = LambdaBackend()
        controller.start("lint")
        self.assertEqual(wait(controller)["results"][-1]["outcome"], "success")

    def test_mismatched_backend_result_recovers(self):
        class WrongBackend:
            def lint(self, source, revision):
                return Result("interpret", revision + 1, "success", "Bad contract")
        controller = Controller(Model(), WrongBackend())
        controller.change("apply", draft="D0Eint(1)")
        controller.start("lint")
        self.assertEqual(wait(controller)["results"][-1]["outcome"], "backend_error")

    def test_upload_rejection_and_replacement(self):
        controller = Controller(Model(), RecordingBackend())
        controller.upload(b"D0Eint(1)", "first.lambda")
        for raw in [b"\xff", b"  ", b"x" * (MAX_SOURCE_BYTES + 1)]:
            with self.subTest(raw_size=len(raw)), self.assertRaises(StateError):
                controller.upload(raw, "bad.lambda")
            self.assertEqual(controller.state()["revision"], 1)
            self.assertEqual(controller.state()["source"], "D0Eint(1)")
        controller.change("factorial")
        self.assertEqual(controller.state()["revision"], 2)
        controller.change("fibonacci")
        self.assertEqual(controller.state()["revision"], 3)
        controller.change("draft", draft="unapplied")
        with self.assertRaises(StateError):
            controller.upload(b"D0Eint(2)", "other.lambda")
        self.assertEqual(controller.state()["draft"], "unapplied")


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(RecordingBackend())
        self.client = self.app.test_client()

    def test_initial_page_controls_and_manual_without_upload(self):
        page = self.client.get("/").get_data(as_text=True)
        for text in ["Choose File", "Manual input", "Factorial (canned)", "Fibonacci (canned)", "Apply changes", "Discard changes"]:
            self.assertIn(text, page)
        positions = [page.index(f'data-operation="{operation}"') for operation in ("lint", "interpret", "typecheck", "compile", "execute")]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.client.post("/api/action/lint", json={}).status_code, 409)
        state = self.client.post("/api/source/apply", json={"draft": "D0Eint(42)"}).get_json()
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["source"], "D0Eint(42)")

    def test_dirty_requests_cannot_bypass_model(self):
        self.client.post("/api/source/apply", json={"draft": "D0Eint(1)"})
        for route in ("/api/action/lint", "/api/source/factorial"):
            response = self.client.post(route, json={"draft": "D0Eint(2)"})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.get_json()["state"]["source"], "D0Eint(1)")
        self.client.post("/api/source/discard", json={})
        self.assertEqual(self.client.post("/api/action/execute", json={}).status_code, 409)

    def test_upload_utf8_and_oversize_transport(self):
        self.client.post("/api/source/apply", json={"draft": "D0Eint(1)"})
        response = self.client.post("/api/source/upload", data={"file": (io.BytesIO(b"\xff"), "bad.lambda")})
        self.assertEqual(response.status_code, 409)
        self.assertIn("UTF-8", response.get_json()["error"])
        response = self.client.post("/api/source/apply", json={"draft": "x" * (1024 * 1024 + 1)})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.get_json()["state"]["source"], "D0Eint(1)")


if __name__ == "__main__":
    unittest.main()
