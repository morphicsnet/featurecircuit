import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

def _try(cmd: list[str]) -> Optional[str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None

def write_run_log(path: str, extra: Optional[Dict[str, Any]] = None) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git": {
            "rev": _try(["git", "rev-parse", "HEAD"]),
            "status": _try(["git", "status", "--porcelain"]),
        },
        "env": {
            "python": _try(["python", "--version"]),
            "rustc": _try(["rustc", "--version"]),
            "cargo": _try(["cargo", "--version"]),
        },
    }
    if extra:
        payload.update(extra)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
