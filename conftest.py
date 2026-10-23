from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for sub in (ROOT / "src", ROOT / "vendor"):
    s = str(sub)
    if s not in sys.path:
        sys.path.insert(0, s)
