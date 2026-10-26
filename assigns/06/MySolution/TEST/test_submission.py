"""Submission portability, independent of the surrounding course checkout."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class SubmissionTests(unittest.TestCase):
    def test_bundled_source_ast_loads_without_assignment_five(self):
        solution = Path(__file__).resolve().parents[1]
        # Keep the temporary target inside this assignment's writable directory.
        with tempfile.TemporaryDirectory(dir=solution.parent) as directory:
            package = Path(directory) / "MySolution"
            package.mkdir()
            for filename in ("__init__.py", "source.py", "lambda1_vp.py"):
                shutil.copyfile(solution / filename, package / filename)
            script = (
                "import sys; sys.path.insert(0, '.'); "
                "from MySolution.source import D0Eint, SOURCE_FILE; "
                "assert D0Eint(3).arg1 == 3; "
                "assert SOURCE_FILE.parent.name == 'MySolution'"
            )
            result = subprocess.run([sys.executable, "-I", "-B", "-c", script],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
