import json
import math
import os

from flask import Flask, jsonify, request

from .errors import RpcError
from .rpc import dispatch, error_response
from .service import LanguageService


def reject_constant(value):
    raise ValueError("nonfinite JSON number")


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite JSON number")
    return result


def create_app(service=None):
    app = Flask(__name__)
    if service is None:
        source_limit = int(os.environ.get("LAMBDA_MAX_SOURCE_BYTES", "65536"))
        timeout = float(os.environ.get("LAMBDA_TIMEOUT_SECONDS", "5"))
        if source_limit < 1 or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Source limit and deadline must be positive and finite")
        service = LanguageService(source_limit, timeout)

    @app.post("/rpc")
    def rpc_endpoint():
        if request.mimetype != "application/json":
            return jsonify({"error": "Content-Type must be application/json"}), 415
        try:
            payload = json.loads(request.get_data().decode("utf-8"),
                                 parse_constant=reject_constant, parse_float=finite_float)
        except (ValueError, UnicodeError, RecursionError):
            response = error_response(None, RpcError(-32700, "Parse error"))
        else:
            response = dispatch(payload, service)
        if response is None:
            return "", 204
        return jsonify(response), 200

    return app
