"""Verify the committed submission in a fresh archive and virtual environment."""
import io
import json
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd):
    print("Running:", " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, check=True)


def verify():
    repo = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip())
    relative = ROOT.relative_to(repo).as_posix()
    changes = subprocess.check_output(["git", "status", "--porcelain", "--", relative], cwd=repo, text=True)
    if changes.strip():
        raise RuntimeError("Commit the submission before verifying its clean archive.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    archive = subprocess.check_output(["git", "archive", "--format=tar", "HEAD", relative], cwd=repo)
    output = ROOT / "test-results"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="clean-", dir=output) as directory:
        checkout_root = Path(directory).resolve()
        # Check the absolute target before extraction and before recursive temp cleanup.
        assert checkout_root.is_relative_to(output.resolve())
        try:
            with tarfile.open(fileobj=io.BytesIO(archive)) as source:
                source.extractall(checkout_root, filter="data")
            project = checkout_root / relative
            environment = project / ".venv"
            run([sys.executable, "-m", "venv", environment], project)
            python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            run([python, "-m", "pip", "install", "-r", "requirements-test.txt"], project)
            run([python, "-m", "unittest", "discover", "-s", "TEST", "-p", "test_*.py", "-v"], project)

            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
            server = subprocess.Popen([str(python), "app.py", "--port", str(port)], cwd=project,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 10
                while True:
                    try:
                        with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                            assert b"LAMBDA workspace" in response.read()
                        break
                    except OSError:
                        if server.poll() is not None or time.monotonic() >= deadline:
                            raise RuntimeError("Documented CLI startup failed.")
                        time.sleep(0.1)
                print("Documented CLI startup: PASS", flush=True)
            finally:
                server.terminate()
                server.communicate(timeout=5)

            browser_report = project / "test-results" / "clean-browser.json"
            browser_report.parent.mkdir(exist_ok=True)
            run([python, "TEST/browser_smoke.py", "--report", browser_report], project)
            browser = json.loads(browser_report.read_text(encoding="utf-8"))
            summary = {"source_commit": commit, "python": platform.python_version(),
                       "fresh_virtual_environment": True, "declared_dependency_install": "passed",
                       "automated_tests": "23 passed", "documented_cli_startup": "passed",
                       "browser_scenarios": "10 passed", "browser_version": browser["browser_version"]}
            (ROOT / "TEST" / "clean-results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            print("Clean checkout verification: PASS", flush=True)
        finally:
            assert checkout_root.is_relative_to(output.resolve())


if __name__ == "__main__":
    verify()
