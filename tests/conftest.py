from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PY = REPO_ROOT / "core" / "protocol" / "python"
DEMO_ROOT = REPO_ROOT / "demo"
CORE_PY_NSI = REPO_ROOT / "core" / "py_nsi"

for p in (str(PROTOCOL_PY), str(DEMO_ROOT), str(CORE_PY_NSI)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("PYTHONWARNINGS", "default")
