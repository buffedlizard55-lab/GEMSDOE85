#!/usr/bin/env python3
"""Resolve the second round of parallel-session conflicts on main (RELIEF lane).

Strategy: **union, never overwrite**.  Every side keeps its content; where the two sides
used the same item namespace, this session's items are renumbered so the numbering stays
unique and both records remain citable.

Files: AI_USE.md, IRREGULARITIES.md, SLOT_PLAN.md, docs/SUBMIT.md (auto-merged),
ledger/submissions.csv, README.md (single CURRENT STATE table).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFLICT = re.compile(r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/main\n", re.S)


def resolve(path: Path, transform=None) -> None:
    text = path.read_text()

    def repl(m: re.Match) -> str:
        head, theirs = m.group(1), m.group(2)
        if transform is not None:
            return transform(head, theirs)
        return head.rstrip("\n") + "\n\n" + theirs.rstrip("\n") + "\n"

    out = CONFLICT.sub(repl, text)
    path.write_text(out)


def main() -> int:
    # ---------------- AI_USE.md: both sessions' disclosures, in file order
    resolve(ROOT / "AI_USE.md")

    # ---------------- IRREGULARITIES.md: renumber this session's items to IR-V2-21..27
    # (the parallel RELIEF session took IR-V2-20)
    def irreg(head: str, theirs: str) -> str:
        head = re.sub(r"^## IR-V2-(\d\d)", lambda m: f"## IR-V2-{int(m.group(1)) + 1:02d}", head,
                      flags=re.M)
        head = head.replace("IR-V2-20 … IR-V2-26", "IR-V2-21 … IR-V2-27")
        head = head.replace("numbered IR-V2-20 … IR-V2-26", "numbered IR-V2-21 … IR-V2-27")
        return head.rstrip("\n") + "\n\n" + theirs.rstrip("\n") + "\n"

    resolve(ROOT / "IRREGULARITIES.md", irreg)

    # ---------------- SLOT_PLAN.md: both "better axes" lists, under separate headings
    def slotplan(head: str, theirs: str) -> str:
        return (head.rstrip("\n") + "\n\n### Also proposed by the parallel RELIEF session "
                "(`arena/3dd0b94c`, 2026-10-23) — not built\n\n" + theirs.rstrip("\n") + "\n")

    resolve(ROOT / "SLOT_PLAN.md", slotplan)

    # ---------------- ledger/submissions.csv: union of both sides' rows
    def ledger(head: str, theirs: str) -> str:
        return head.rstrip("\n") + "\n" + theirs.rstrip("\n") + "\n"

    resolve(ROOT / "ledger" / "submissions.csv", ledger)

    # ---------------- README.md: one CURRENT STATE table, both sessions' rows
    readme = (ROOT / "README.md").read_text()

    def readme_fix(m: re.Match) -> str:
        head, theirs = m.group(1), m.group(2)
        if head.startswith("## CURRENT STATE"):
            return ("## CURRENT STATE (2026-10-23, after PRUNE, PRUNE-rungs, SNAP, verification, "
                    "RELIEF and the CONCENTRATION sessions `arena/28da814f` / `arena/3dd0b94c` / "
                    "`arena/c4de5673`)\n")
        # table-body conflict: keep the RELIEF session's rows, then this session's rows
        keep = []
        for line in theirs.rstrip("\n").splitlines():
            keep.append(line)
        extra = [ln for ln in head.rstrip("\n").splitlines()
                 if ln.startswith("| **CONCENTRATION variants")]
        axis = [ln for ln in head.rstrip("\n").splitlines() if ln.startswith("| **AXIS status**")]
        nextrow = [ln for ln in head.rstrip("\n").splitlines()
                   if ln.startswith("| **next 3 slots** (human-assigned axis = CONCENTRATION)")]
        out = "\n".join(keep)
        if axis:
            out += "\n" + axis[0]
        if extra:
            out += "\n" + extra[0]
        if nextrow:
            out += "\n" + nextrow[0]
        return out

    readme = CONFLICT.sub(readme_fix, readme)
    (ROOT / "README.md").write_text(readme)
    print("resolved: AI_USE.md, IRREGULARITIES.md, SLOT_PLAN.md, ledger/submissions.csv, README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
