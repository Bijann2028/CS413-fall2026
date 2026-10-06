"""Transport-independent language-tool contract."""
from dataclasses import dataclass, field
from typing import Literal, Protocol

Outcome = Literal["success", "input_error", "language_error", "runtime_error",
                  "backend_error", "timeout", "not_implemented"]
OPERATIONS = ("lint", "interpret", "typecheck", "compile", "execute")
MAX_SOURCE_BYTES = 64 * 1024


@dataclass(frozen=True)
class Artifact:
    revision: int
    target: str
    code: bytes
    # Future Execute accepts this exact artifact; it never recompiles source.


@dataclass(frozen=True)
class Result:
    operation: str
    revision: int
    outcome: Outcome
    text: str
    free_variables: frozenset[str] = field(default_factory=frozenset)
    artifact: Artifact | None = None

    def public(self):
        return {"operation": self.operation, "revision": self.revision,
                "outcome": self.outcome, "text": self.text,
                "free_variables": sorted(self.free_variables)}


class Backend(Protocol):
    def lint(self, source: str, revision: int) -> Result: ...
    def interpret(self, source: str, revision: int) -> Result: ...
    def typecheck(self, source: str, revision: int) -> Result: ...
    def compile(self, source: str, revision: int) -> Result: ...
    def execute(self, artifact: Artifact) -> Result: ...
