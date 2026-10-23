#!/usr/bin/env python3
"""Retired lane-specific run-card writer; refresh only the current blocked state."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from preflight import write_preflight_state  # noqa: E402


def main() -> int:
    card = write_preflight_state(ROOT)
    print("BLOCKED: lane-specific historical run-card assembly is retired.")
    print("Wrote only evidence/run_card.json and registry/submission.json in negative preflight state.")
    print("No candidate, experiment, or submission slot was created or selected.")
    for blocker in card["blockers"]:
        print(f"- {blocker}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
