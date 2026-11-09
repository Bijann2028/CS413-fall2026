"""Framework-independent JSON-RPC envelope and batch handling."""
import logging
import math

from .errors import RpcError

LOG = logging.getLogger(__name__)


def error_response(request_id, error):
    return {"jsonrpc": "2.0", "id": request_id, "error": error.payload()}


def valid_id(value):
    return (value is None or isinstance(value, str) or type(value) is int
            or (type(value) is float and math.isfinite(value)))


def valid_envelope(request):
    if not isinstance(request, dict):
        return False
    if request.get("jsonrpc") != "2.0":
        return False
    if not isinstance(request.get("method"), str):
        return False
    return "id" not in request or valid_id(request["id"])


def dispatch_one(request, service):
    if not valid_envelope(request):
        return error_response(None, RpcError(-32600, "Invalid Request"))
    notification = "id" not in request
    request_id = request.get("id")
    try:
        result = service.call(request["method"], request.get("params"))
        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
    except RpcError as error:
        response = error_response(request_id, error)
    except Exception:
        LOG.exception("RPC backend failed")
        response = error_response(request_id, RpcError(-32603, "Internal error"))
    # Missing ID suppresses success and error alike; explicit null never does.
    return None if notification else response


def dispatch(payload, service):
    if not isinstance(payload, list):
        return dispatch_one(payload, service)
    if not payload:
        return error_response(None, RpcError(-32600, "Invalid Request"))
    responses = [dispatch_one(item, service) for item in payload]
    return [item for item in responses if item is not None] or None
