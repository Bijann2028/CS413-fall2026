"""Bound the whole worker lifetime, then read its completed JSON result."""
import json
import logging
import multiprocessing as mp
from pathlib import Path
import tempfile
import time

from .errors import RpcError
from .service import perform

LOG = logging.getLogger(__name__)


def interpretation_worker(result_path, params):
    try:
        result = {"result": perform("lambda.interpret", params)}
    except RpcError as error:
        result = {"error": error.payload()}
    except Exception:
        LOG.exception("Interpretation worker failed")
        result = {"error": {"code": -32603, "message": "Internal error"}}
    Path(result_path).write_text(json.dumps(result), encoding="utf-8")


def run_interpretation(params, timeout_seconds, worker_target=interpretation_worker):
    context = mp.get_context("spawn")
    # A pipe can become readable before an entire result is available. Waiting
    # for worker exit before reading a private file keeps result writes within
    # the deadline and avoids both partial-read and pipe-buffer deadlocks.
    with tempfile.TemporaryDirectory(prefix="lambda-rpc-") as directory:
        result_path = Path(directory) / "result.json"
        process = context.Process(target=worker_target,
                                  args=(str(result_path), params), daemon=True)
        deadline = time.monotonic() + timeout_seconds
        try:
            process.start()
            process.join(max(0, deadline - time.monotonic()))
            if process.is_alive():
                raise RpcError(-32012, "Execution timeout",
                               {"timeout_seconds": timeout_seconds})
            if process.exitcode != 0:
                LOG.error("Interpretation worker exited with code %s", process.exitcode)
                raise RpcError(-32603, "Internal error")
            try:
                payload = json.loads(result_path.read_text(encoding="utf-8"))
                if "error" in payload:
                    error = payload["error"]
                    raise RpcError(error["code"], error["message"], error.get("data"))
                return payload["result"]
            except (OSError, ValueError, KeyError, TypeError):
                LOG.exception("Interpretation worker produced an invalid result")
                raise RpcError(-32603, "Internal error") from None
        finally:
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join()
                process.close()
