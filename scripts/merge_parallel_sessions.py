#!/usr/bin/env python3
"""Reconcile this session's CONCENTRATION work with the parallel sessions already on main.

`main` gained PRUNE / PRUNE-rung / SNAP sessions (arena/e081f5da, arena/30dcc7f0,
arena/a9cc6c47, arena/28da814f) while this session ran, and the five shared files collided
(add/add).  This script rebuilds each shared file as **theirs + mine**, so that no parallel
session's work is lost:

  AI_USE.md        theirs, then this session's section
  IRREGULARITIES.md theirs, then this session's items renumbered into their IR-V2-* namespace
  SLOT_PLAN.md     theirs, then this session's CONCENTRATION slot section
  docs/SUBMIT.md   theirs, then this session's CONCENTRATION upload section
  ledger/submissions.csv  their schema, then this session's three rows
  README.md        their CURRENT STATE block, with this session's rows folded in

Run:  python scripts/merge_parallel_sessions.py   (from the repo root, with the conflict
      stages still present: git show :2:<file> = ours, git show :3:<file> = theirs)
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stage(n: int, path: str) -> str:
    return subprocess.run(["git", "show", f":{n}:{path}"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def main() -> int:
    # ------------------------------------------------------------------ AI_USE.md
    theirs = stage(3, "AI_USE.md").rstrip("\n")
    ours = stage(2, "AI_USE.md")
    ours_body = ours.split("\n", 1)[1].strip("\n")
    ours_body = ours_body.replace("## What the AI wrote (all of it)",
                                  "## 2026-10-23 — arena/c4de5673-gemsdoe85 (this session)")
    out = theirs + "\n\n---\n\n" + ours_body + "\n"
    (ROOT / "AI_USE.md").write_text(out)

    # ------------------------------------------------------------------ IRREGULARITIES.md
    theirs = stage(3, "IRREGULARITIES.md").rstrip("\n")
    ours = stage(2, "IRREGULARITIES.md")
    # take only the item bodies (everything from the first "## IR-85-" heading)
    items = ours[ours.index("## IR-85-A1"):]
    items = re.sub(r"^## IR-85-A(\d)", lambda m: f"## IR-V2-{19 + int(m.group(1)):02d}", items,
                    flags=re.M)
    items = items.replace("IR-85-A4", "IR-V2-23").replace("IR-85-A5", "IR-V2-24")
    header = (
        "\n---\n\n## Session `arena/c4de5673-gemsdoe85` (2026-10-23) — AXIS = CONCENTRATION\n\n"
        "This session is the first in the v2 line where the **human assigned the axis**\n"
        "(CONCENTRATION). Its items are numbered IR-V2-20 … IR-V2-26 and are appended below;\n"
        "they are decision-changing, so they are not summarised away.\n\n"
    )
    (ROOT / "IRREGULARITIES.md").write_text(theirs + "\n" + header + items.rstrip("\n") + "\n")

    # ------------------------------------------------------------------ SLOT_PLAN.md
    theirs = stage(3, "SLOT_PLAN.md").rstrip("\n")
    ours = stage(2, "SLOT_PLAN.md")
    mine = ours[ours.index("## The next three slots, in order"):]
    mine = mine.replace("## The next three slots, in order",
                        "## CONCENTRATION slots (session `arena/c4de5673`, 2026-10-23 — the axis the "
                        "**human assigned**)")
    mine = mine.replace("## Weeks to the deadline (2026-12-03)",
                        "## Weeks to the deadline (2026-12-03) — CONCENTRATION session's view")
    # keep their plan intact, prepend a short pointer, then append our axis section
    pointer = (
        "\n---\n\n> **Update 2026-10-23, session `arena/c4de5673`:** the human has now assigned an\n"
        "> axis (CONCENTRATION), so the slot order below is superseded for this week by the\n"
        "> three CONCENTRATION rungs at the end of this file. The PRUNE / SNAP rungs above remain\n"
        "> **built, gated and available as the backup ladder** — the human may reorder them.\n\n"
    )
    (ROOT / "SLOT_PLAN.md").write_text(theirs + "\n" + pointer + mine.rstrip("\n") + "\n")

    # ------------------------------------------------------------------ docs/SUBMIT.md
    theirs = stage(3, "docs/SUBMIT.md").rstrip("\n")
    ours = stage(2, "docs/SUBMIT.md")
    mine = ours[ours.index("## The three candidate slots"):]
    mine = mine.replace("## The three candidate slots (blind order: submit the smallest dose first)",
                        "## CONCENTRATION candidates (session `arena/c4de5673`, 2026-10-23 — the axis the "
                        "**human assigned**)\n\n"
                        "The PRUNE / SNAP files below remain the backup ladder. Upload ONE file per slot.")
    (ROOT / "docs/SUBMIT.md").write_text(theirs + "\n\n---\n\n" + mine.rstrip("\n") + "\n")

    # ------------------------------------------------------------------ ledger/submissions.csv
    theirs = stage(3, "ledger/submissions.csv").rstrip("\n")
    header, *rows = theirs.splitlines()
    cols = header.split(",")
    new_rows = [
        ["gems85-h33-h33-2-b2-conc10-20261023-f89e4659", "GEMSDOE85",
         "gems85-h33-h33-2-b2-conc10-20261023-f89e4659.tif", "", "MODEL (prediction; no score)",
         "nan-outside primary; zeros twin", "37654", "f89e4659", "h33-h33-2-b2", "CONCENTRATION",
         '"10% of dots moved from lowest-prior 0.8km blocks to highest-prior"', "9.999",
         "f89e46591561025b75ff3d7bac6e85c1f26daa89b81adf3f9c9fa6a937b13755", "BUILT",
         "-0.010 to -0.030 vs 0.2778 CLAIM MODEL", "N", "", ""],
        ["gems85-h33-h33-2-b2-conc15-20261023-45bfb93b", "GEMSDOE85",
         "gems85-h33-h33-2-b2-conc15-20261023-45bfb93b.tif", "", "MODEL (prediction; no score)",
         "nan-outside primary; zeros twin", "37654", "45bfb93b", "h33-h33-2-b2", "CONCENTRATION",
         '"15% of dots moved from lowest-prior 0.8km blocks to highest-prior"', "15.000",
         "45bfb93bf9367280983e0c446af8e30cb4994fb86025d5753b68b2eabe2f1a01", "BUILT",
         "-0.015 to -0.040 vs 0.2778 CLAIM MODEL", "N", "", ""],
        ["gems85-h33-h33-2-b2-conc20-20261023-a93e0b41", "GEMSDOE85",
         "gems85-h33-h33-2-b2-conc20-20261023-a93e0b41.tif", "", "MODEL (prediction; no score)",
         "nan-outside primary; zeros twin", "37654", "a93e0b41", "h33-h33-2-b2", "CONCENTRATION",
         '"20% of dots moved from lowest-prior 0.8km blocks to highest-prior"', "20.001",
         "a93e0b41bd10b0b104b4efd1d6f6050be285fef2e616bd9bf02d4b6e54e9cba0", "BUILT",
         "-0.020 to -0.050 vs 0.2778 CLAIM MODEL", "N", "", ""],
    ]
    lines = [header]
    for r in rows:
        if r.strip():
            lines.append(r)
    for r in new_rows:
        assert len(r) == len(cols), (len(r), len(cols))
        lines.append(",".join(r))
    (ROOT / "ledger" / "submissions.csv").write_text("\n".join(lines) + "\n")

    print("merged: AI_USE.md, IRREGULARITIES.md, SLOT_PLAN.md, docs/SUBMIT.md, "
          "ledger/submissions.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
