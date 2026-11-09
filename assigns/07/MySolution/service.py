"""Thin adapter; language semantics remain in the provided implementation."""
import re
import sys
from pathlib import Path

from .errors import RpcError

LANGUAGE_DIR = Path(__file__).resolve().parents[1] / "LAMBDA3"
sys.path.insert(0, str(LANGUAGE_DIR))
import lambda3 as L

METHODS = {"service.health", "lambda.typecheck", "lambda.interpret", "lambda.compile"}


def invalid(reason):
    raise RpcError(-32602, "Invalid params", {"reason": reason})


def validate_params(method, params, max_source_bytes):
    if not isinstance(params, dict):
        invalid("params must be an object")
    expected = set() if method == "service.health" else {"source"}
    if method == "lambda.compile":
        expected.add("target")
    if set(params) != expected:
        invalid("params must contain exactly: " + ", ".join(sorted(expected)))
    if "source" in expected:
        source = params["source"]
        if not isinstance(source, str) or not source.strip():
            invalid("source must be a nonblank string")
        try:
            size = len(source.encode("utf-8"))
        except UnicodeEncodeError:
            invalid("source must contain valid Unicode")
        if size > max_source_bytes:
            invalid(f"source exceeds {max_source_bytes} UTF-8 bytes")
    if method == "lambda.compile" and params["target"] not in ("python", "javascript"):
        invalid("target must be python or javascript")


def diagnostic(error):
    text = str(error).split("\n")[0]
    # Paths may contain spaces or be UNC names. Once a path starts, omit the
    # rest of the line rather than exposing a trailing part of a filename.
    text = re.sub(r"(?:[A-Za-z]:[\\/]|\\\\|/(?=[\w.]))[^\r\n]*",
                  "[path omitted]", text)
    return text[:500]


def perform(method, params):
    try:
        expression, typ = L.d0exp_parse_and_typecheck(params["source"])
        if method == "lambda.typecheck":
            return {"type": L.format_type(typ)}
        if method == "lambda.interpret":
            return {"type": L.format_type(typ),
                    "value": L.d0val_format(L.d0exp_evaluate(expression))}
        target = params["target"]
        compile_fn = L.d0exp_compile if target == "python" else L.d0exp_compile_js
        return {"target": target, "code": compile_fn(expression)}
    except L.LambdaSyntaxError as error:
        raise RpcError(-32010, "LAMBDA syntax error", {"diagnostic": diagnostic(error)}) from None
    except L.TypeCheckError as error:
        raise RpcError(-32011, "LAMBDA type error", {"diagnostic": diagnostic(error)}) from None


class LanguageService:
    def __init__(self, max_source_bytes=65536, timeout_seconds=5.0):
        self.max_source_bytes = max_source_bytes
        self.timeout_seconds = timeout_seconds

    def call(self, method, params):
        if method not in METHODS:
            raise RpcError(-32601, "Method not found")
        validate_params(method, params, self.max_source_bytes)
        if method == "service.health":
            return {"status": "ok", "version": "1.0"}
        if method == "lambda.interpret":
            from .worker import run_interpretation
            return run_interpretation(params, self.timeout_seconds)
        return perform(method, params)
