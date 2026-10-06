"""Coordinate source workflow and backend requests without rendering code."""
from pathlib import Path
from threading import Thread
from contracts import Backend, MAX_SOURCE_BYTES, Result
from model import Model, StateError

SAMPLES = Path(__file__).with_name("samples")


class Controller:
    def __init__(self, model: Model, backend: Backend):
        self.model = model
        self.backend = backend

    def state(self):
        with self.model.lock:
            return self.model.public()

    def change(self, action, draft=None, text=None, name=None):
        with self.model.lock:
            if draft is not None:
                self.model.edit(draft)
            if action == "draft":
                return self.model.public()
            if action == "apply":
                self.model.apply()
            elif action == "discard":
                self.model.discard()
            elif action == "manual":
                self.model.manual()
            elif action in ("factorial", "fibonacci"):
                self.model.replace((SAMPLES / f"{action}.lambda").read_text(encoding="utf-8"), action.capitalize())
            elif action == "upload":
                self.model.replace(text, name or "Uploaded source")
            else:
                raise StateError("Unknown source action.")
            return self.model.public()

    def upload(self, raw, name, draft=None):
        with self.model.lock:
            if draft is not None:
                self.model.edit(draft)
            self.model.clean()
            if len(raw) > MAX_SOURCE_BYTES:
                raise StateError("Source exceeds 65,536 UTF-8 bytes.")
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise StateError("Uploaded file is not valid UTF-8.") from exc
            return self.change("upload", text=text, name=name)

    def start(self, operation, draft=None):
        with self.model.lock:
            if draft is not None:
                self.model.edit(draft)
            source, revision, artifact = self.model.begin(operation)
            Thread(target=self._work, args=(operation, source, revision, artifact), daemon=True).start()
            return self.model.public()

    def _work(self, operation, source, revision, artifact):
        try:
            method = getattr(self.backend, operation)
            result = method(artifact) if operation == "execute" else method(source, revision)
            if not isinstance(result, Result):
                raise TypeError("Backend must return Result.")
        except Exception as exc:
            result = Result(operation, revision, "backend_error", f"Backend failed: {type(exc).__name__}: {exc}")
        with self.model.lock:
            try:
                self.model.finish(result)
            except StateError as exc:
                self.model.finish(Result(operation, revision, "backend_error", str(exc)))
