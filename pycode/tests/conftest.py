"""
conftest.py — pytest configuration for pycode/tests/.

Ensures pycode/ is on sys.path so that ``import extract`` and
``import nb_to_report`` work regardless of from where pytest is invoked
(e.g. repo root, CI runner, or directly from this directory).
"""
import sys
from pathlib import Path

# pycode/ lives one level above this conftest
_pycode = Path(__file__).parent.parent
if str(_pycode) not in sys.path:
    sys.path.insert(0, str(_pycode))
