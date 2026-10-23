#!/usr/bin/env python3
"""Restore + SHA-256 verify ONLY the inputs this axis session reads.

`scripts/restore_data.py` cannot fetch these entries: the core/external/scored manifest
dests contain sub-directories, and that script rejects sub-paths unless the manifest entry
is flagged `_subdirs` (only the geothermal and learning manifests are).  Rather than change
a shared script mid-session, this helper pins the exact (dest, repo, path, sha256) tuples
this session depends on, verifies them against `registry/data_manifest.json` /
`registry/scored_artifacts.json`, and streams the bytes with the authenticated `gh` CLI.

Never contacts DrivenData or dropbox.  Idempotent: an existing file with the pinned
SHA-256 is reported `present` and left untouched.

Usage:  python3 scripts/restore_axis_inputs.py [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"

# (dest relative to repo root, source repo, path inside that repo, sha256)
SPEC = [
    # H19-5 ridge skeleton -> d2.8 thinning -> R0 (pinned manifest entries, group "scored")
    ("data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
     "GEMSDOE24", "inputs/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
     "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"),
    ("data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
     "GEMSDOE24", "docs/downloads/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
     "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"),
    # lineage witnesses used as rebuild assertions (never as inputs to the variants)
    ("data/registry_rasters/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
     "GEMSDOE31", "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
     "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"),
    ("data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif",
     "GEMSDOE32", "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif",
     "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"),
    ("data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
     "GEMSDOE32", "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
     "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    # report-only PROXY truth layer (SGMC faults); never an input to a candidate mask
    ("data/external/derived_sgmc_faults_100m_u8.tif",
     "GEMSDOE24", "data/external/derived_sgmc_faults_100m_u8.tif",
     "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
]

# Already tracked in this repo; verified here so the receipt is self-contained.
PRESENT = [
    ("data/labels.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    ("data/existing_faults.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    ("data/sample_submission.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_against_registry() -> dict:
    """Cross-check every SPEC sha256 against the repo's own pinned registries."""
    man = json.loads((ROOT / "registry" / "data_manifest.json").read_text())["files"]
    scored = json.loads((ROOT / "registry" / "scored_artifacts.json").read_text())["artifacts"]
    sys.path.insert(0, str(ROOT / "src"))
    from gems85.r0_lineage import PINS as LINEAGE_PINS          # noqa: PLC0415
    known = {f["sha256"] for f in man} | {a["sha256"] for a in scored}
    known |= set(LINEAGE_PINS.values())
    known |= {s for _, s in PRESENT}
    bad = [(d, s) for d, _, _, s in SPEC if s not in known]
    if bad:
        raise SystemExit(f"spec sha256 not pinned in registry: {bad}")
    return {"n_manifest": len(man), "n_scored_artifacts": len(scored), "n_spec": len(SPEC)}


def fetch(repo: str, path: str, dest: Path, expect: str, force: bool) -> dict:
    if dest.is_file() and not force:
        got = sha256_file(dest)
        if got == expect:
            return dict(dest=str(dest.relative_to(ROOT)), status="present", sha256=got,
                        bytes=dest.stat().st_size)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest.parent, suffix=".partial", delete=False) as tf:
        tmp = Path(tf.name)
        try:
            subprocess.run(
                ["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}",
                 "-H", "Accept: application/vnd.github.raw"],
                stdout=tf, check=True, timeout=900,
            )
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
    try:
        got = sha256_file(tmp)
        if got != expect:
            raise ValueError(f"sha256 {got} != pinned {expect} for {dest}")
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dict(dest=str(dest.relative_to(ROOT)), status="restored", sha256=got,
                bytes=dest.stat().st_size)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    reg = verify_against_registry()
    print(f"registry cross-check: {reg}")
    rows = []
    for rel, repo, path, expect in SPEC:
        try:
            r = fetch(repo, path, ROOT / rel, expect, args.force)
        except Exception as exc:                                   # noqa: BLE001
            print(f"[FAIL]     {rel}: {exc}", file=sys.stderr)
            rows.append(dict(dest=rel, status="FAILED", error=str(exc), expected_sha256=expect))
            continue
        print(f"[{r['status']:8s}] {rel}  {r['sha256'][:16]}  {r['bytes']} B")
        rows.append({**r, "expected_sha256": expect})
    for rel, expect in PRESENT:
        got = sha256_file(ROOT / rel)
        ok = got == expect
        print(f"[{'present' if ok else 'MISMATCH'}] {rel}  {got[:16]}")
        rows.append(dict(dest=rel, status="present" if ok else "FAILED", sha256=got,
                         expected_sha256=expect, bytes=(ROOT / rel).stat().st_size))
    out = ROOT / "evidence" / "axis_inputs_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"registry_cross_check": reg, "files": rows}, indent=2) + "\n")
    bad = [r for r in rows if r["status"] == "FAILED"]
    print(f"\n{len(rows) - len(bad)}/{len(rows)} verified -> {out.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
