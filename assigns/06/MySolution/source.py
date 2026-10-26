"""Load the bundled, unchanged course AST with one canonical module identity.

lambda1_vp.py is copied byte-for-byte from Assignment 5 so this submission
also works without sibling assignment directories. Its evaluator is not used.
"""

import importlib.util
from pathlib import Path
import sys

SOURCE_FILE = Path(__file__).resolve().with_name("lambda1_vp.py")
if "lambda1_vp" not in sys.modules:
    spec = importlib.util.spec_from_file_location("lambda1_vp", SOURCE_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from lambda1_vp import (  # noqa: E402 -- initialize the course module first
    D0E000, D0Eint, D0Ebtf, D0Evar, D0Elam, D0Eapp, D0Efix,
    D0Eop1, D0Eop2, D0Eif0, D0Elet, D0Epair, D0Epfst, D0Epsnd,
    D0ExpVisitor, FreeVariableVisitor, d0exp_fvset,
)
