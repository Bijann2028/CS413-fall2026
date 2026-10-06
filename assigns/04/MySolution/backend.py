"""Replaceable adapter to the supplied interpreter, isolated from HTTP and HTML."""
import json
from pathlib import Path
import subprocess
import sys
from contracts import Artifact, Result

TIMEOUT_SECONDS = 3.0


class LambdaBackend:
    def __init__(self, timeout=TIMEOUT_SECONDS):
        self.timeout = timeout

    def _run(self, operation, source, revision):
        try:
            process = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("worker.py"))],
                input=json.dumps({"operation": operation, "source": source}),
                capture_output=True, text=True, encoding="utf-8", timeout=self.timeout,
                cwd=Path(__file__).parent,
            )
            if process.returncode:
                return Result(operation, revision, "backend_error",
                              f"Language worker exited with code {process.returncode}.")
            payload = json.loads(process.stdout)
            return Result(operation, revision, payload["outcome"], payload["text"],
                          frozenset(payload.get("free_variables", [])))
        except subprocess.TimeoutExpired:
            return Result(operation, revision, "timeout",
                          f"Operation exceeded {self.timeout:g} seconds; worker terminated. You can retry.")
        except (OSError, ValueError, KeyError) as exc:
            return Result(operation, revision, "backend_error", f"Backend unavailable: {exc}")

    def lint(self, source, revision):
        return self._run("lint", source, revision)

    def interpret(self, source, revision):
        return self._run("interpret", source, revision)

    def typecheck(self, source, revision):
        return Result("typecheck", revision, "not_implemented", "Type checking is not yet implemented.")

    def compile(self, source, revision):
        return Result("compile", revision, "not_implemented", "Compilation is not yet implemented.")

    def execute(self, artifact: Artifact):
        return Result("execute", artifact.revision, "not_implemented",
                      "Generated-code execution is not yet implemented.")
