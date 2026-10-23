#!/usr/bin/env python3
"""Retired historical promotion writer; writes only the current blocked state.

The previous implementation could overwrite canonical submission metadata and
publish a prior session as primary. It is intentionally fail-closed until an
explicit lane and all protocol gates are resolved.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from preflight import write_preflight_state  # noqa: E402


def main() -> int:
    card = write_preflight_state(ROOT)
    print("BLOCKED: no current candidate run card can be assembled.")
    print("Canonical run card and submission registry remain negative; no slot used.")
    for blocker in card["blockers"]:
        print(f"- {blocker}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
