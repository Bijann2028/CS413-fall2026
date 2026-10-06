"""Application state and invariants; no HTTP, rendering, or interpreter imports."""
from dataclasses import dataclass, field
from threading import RLock
from contracts import Artifact, MAX_SOURCE_BYTES, OPERATIONS, Result


class StateError(ValueError):
    pass


@dataclass
class Model:
    source: str | None = None
    name: str = "Manual input"
    revision: int = 0
    draft: str = ""
    manual_pending: bool = False
    results: list[Result] = field(default_factory=list)
    artifact: Artifact | None = None
    busy: str | None = None
    message: str = "Enter code or choose a source."
    lock: RLock = field(default_factory=RLock, repr=False)

    @property
    def dirty(self):
        return self.manual_pending or self.draft != (self.source or "")

    def idle(self):
        if self.busy:
            raise StateError("An operation is busy; wait for completion.")

    def clean(self):
        self.idle()
        if self.dirty:
            raise StateError("Apply or discard changes before continuing.")

    def edit(self, text):
        self.idle()
        if not isinstance(text, str):
            raise StateError("Editor contents must be text.")
        self.draft = text

    def validate(self, text):
        if not text.strip():
            raise StateError("Source must not be empty or whitespace-only.")
        try:
            size = len(text.encode("utf-8"))
        except UnicodeEncodeError as exc:
            raise StateError("Source must be valid UTF-8 text.") from exc
        if size > MAX_SOURCE_BYTES:
            raise StateError("Source exceeds 65,536 UTF-8 bytes.")

    def _accept(self, text, name):
        self.source = self.draft = text
        self.name = name
        self.manual_pending = False
        self.revision += 1
        self.results.clear()
        self.artifact = None
        self.message = "Source applied. Ready."

    def replace(self, text, name):
        self.clean()
        self.validate(text)
        self._accept(text, name)

    def manual(self):
        self.clean()
        self.draft = ""
        self.manual_pending = True
        self.message = "Manual input: enter code, then Apply changes."

    def apply(self):
        self.idle()
        self.validate(self.draft)
        self._accept(self.draft, "Manual input" if self.manual_pending else self.name)

    def discard(self):
        self.idle()
        self.draft = self.source or ""
        self.manual_pending = False
        self.message = "Changes discarded."

    def begin(self, operation):
        self.clean()
        if operation not in OPERATIONS:
            raise StateError("Unknown action.")
        if self.source is None:
            raise StateError("Apply a source before running an action.")
        if operation == "execute" and (self.artifact is None or self.artifact.revision != self.revision):
            raise StateError("Execute requires generated code for the current revision.")
        if operation == "compile":
            self.artifact = None
        self.busy = operation
        self.message = f"Busy: {operation}."
        return self.source, self.revision, self.artifact

    def finish(self, result):
        if result.operation != self.busy or result.revision != self.revision:
            raise StateError("Backend result does not match the active action and revision.")
        if result.artifact is not None:
            if result.operation != "compile" or result.outcome != "success" or result.artifact.revision != self.revision:
                raise StateError("Invalid generated-code artifact.")
            self.artifact = result.artifact
        self.results.append(result)
        self.busy = None
        self.message = "Ready."

    def public(self):
        return {"source": self.source, "name": self.name, "revision": self.revision,
                "draft": self.draft, "dirty": self.dirty, "manual_pending": self.manual_pending, "busy": self.busy,
                "message": self.message, "has_artifact": self.artifact is not None,
                "results": [result.public() for result in self.results]}
