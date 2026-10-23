#!/usr/bin/env python3
"""Retired historical exporter.

This file previously re-emitted a prior-session field into docs/downloads without
consulting the current lane/cache/saturation preflight. It is intentionally
fail-closed. Do not use historical rasters as new submissions.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from preflight import write_preflight_state  # noqa: E402


def main() -> int:
    card = write_preflight_state(ROOT)
    print("BLOCKED: no authorized method lane/cache or literal uniqueness clearance.")
    print("No TIFF written; no experiment run; no submission slot used.")
    print("Current blockers:")
    for blocker in card["blockers"]:
        print(f"- {blocker}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
