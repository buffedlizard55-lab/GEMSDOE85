#!/usr/bin/env python3
"""Restore + SHA-256 verify competition, external geothermal/3DEP, and scored witness files.

Preserves strict path-containment and atomic size+SHA-256 verification invariants:
  - `restore(entry, target_dir)` rejects any `dest` that escapes `target_dir` or traverses
    directories unless `allow_subdirs=True` is explicitly passed for root-relative manifests,
  - never touches an existing valid or pre-existing file if download size or SHA-256 mismatches
    (raises `ValueError('Size/hash mismatch ...')` and cleans up `.partial`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest.json"
MANIFEST_H85 = ROOT / "registry" / "data_manifest_h85.json"
MANIFEST_GEO = ROOT / "registry" / "geothermal_external_manifest.json"
DATA = ROOT / "data"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Alias required by shared template helper `scripts/preflight.py` (fixes IR-85-012)
sha256 = sha256_file


def gh_raw(repo: str, ref: str, path: str, out_fh) -> None:
    """Stream one file from GitHub using the authenticated gh CLI (raw media type)."""
    subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/contents/{path}?ref={ref}",
            "-H",
            "Accept: application/vnd.github.raw",
        ],
        stdout=out_fh,
        check=True,
    )


def restore(
    entry: dict,
    target_dir: Path | None = None,
    *,
    force: bool = False,
    allow_subdirs: bool = False,
) -> dict:
    base = DATA if target_dir is None else Path(target_dir)
    dest_name = entry.get("dest") or entry.get("local_path") or ""
    p_rel = Path(dest_name)
    if p_rel.is_absolute() or ".." in p_rel.parts:
        raise ValueError(f"{entry['id']}: dest must be a single local filename inside target_dir")
    if not allow_subdirs and (len(p_rel.parts) != 1 or p_rel.name != dest_name):
        raise ValueError(f"{entry['id']}: dest must be a single local filename, got {dest_name!r}")

    dest = (ROOT / p_rel) if entry.get("local_path") else (base / p_rel)
    exp_bytes = entry.get("bytes")
    if dest.exists() and not force:
        got = sha256_file(dest)
        size_ok = (exp_bytes is None) or (dest.stat().st_size == exp_bytes)
        if size_ok and got == entry["sha256"]:
            return {
                "id": entry["id"],
                "status": "present",
                "sha256": got,
                "bytes": dest.stat().st_size,
            }

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        with tmp.open("wb") as out:
            for p in entry.get("parts", [entry.get("path") or entry.get("remote_path")]):
                if p is None:
                    raise ValueError(f"{entry['id']}: manifest has neither 'path' nor 'parts'")
                gh_raw(entry["repo"], entry.get("ref") or entry["commit"], p, out)
        got_size = tmp.stat().st_size
        got = sha256_file(tmp)
        size_mismatch = (exp_bytes is not None) and (got_size != exp_bytes)
        if size_mismatch or got != entry["sha256"]:
            raise ValueError(
                f"{entry['id']}: Size/hash mismatch (expected {exp_bytes}B/{entry['sha256']}, "
                f"got {got_size}B/{got})"
            )
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()
    return {
        "id": entry["id"],
        "status": "restored",
        "sha256": got,
        "bytes": dest.stat().st_size,
    }


def _ensure_data_symlinks() -> None:
    raw_dir = DATA / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for stem in ("training_features.tif", "labels.tif", "existing_faults.tif", "sample_submission.tif"):
        top = DATA / stem
        raw = raw_dir / stem
        if raw.is_file() and not top.exists():
            top.symlink_to(Path("raw") / stem)
        elif top.is_file() and not raw.exists():
            raw.symlink_to(Path("..") / stem)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--groups",
        nargs="*",
        default=["core", "external"],
        help="manifest groups to restore (core, external, scored, all).",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    files = [
        {
            **f,
            "group": f.get("group", "core"),
            "_target": DATA if "/" in f.get("dest", "") else DATA / "raw",
            "_subdirs": "/" in f.get("dest", ""),
        }
        for f in manifest["files"]
    ]
    if MANIFEST_GEO.is_file():
        files.extend(
            [{**f, "_target": DATA, "_subdirs": True} for f in json.loads(MANIFEST_GEO.read_text()).get("files", [])]
        )
    if MANIFEST_H85.is_file():
        for f in json.loads(MANIFEST_H85.read_text()).get("files", []):
            if "learning" in f.get("local_path", ""):
                files.append({**f, "group": "scored", "_target": ROOT, "_subdirs": True})

    if args.list:
        for f in files:
            target = f.get("local_path") or f"data/{f['dest']}"
            print(f"{f['id']:46s} {f.get('group',''):9s} {f.get('bytes',0)/1e6:8.1f} MB  -> {target}")
        return 0

    groups = set(args.groups)
    sel = files if "all" in groups else [f for f in files if f.get("group") in groups]
    receipts = []
    for entry in sel:
        try:
            r = restore(
                entry,
                entry.get("_target", DATA),
                force=args.force,
                allow_subdirs=bool(entry.get("_subdirs", False)),
            )
        except Exception as exc:  # noqa: BLE001
            r = {"id": entry["id"], "status": "FAILED", "error": str(exc)}
            print(f"[FAIL] {entry['id']}: {exc}", file=sys.stderr)
        else:
            print(f"[{r['status']:8s}] {r['id']:46s} {r['bytes']/1e6:8.1f} MB  {r['sha256'][:16]}")
        receipts.append(r)

    _ensure_data_symlinks()
    out = ROOT / "registry" / "restore_receipt.json"
    out.write_text(json.dumps({"groups": sorted(groups), "files": receipts}, indent=2) + "\n")
    bad = [r for r in receipts if r["status"] == "FAILED"]
    print(f"\n{len(receipts)-len(bad)}/{len(receipts)} verified -> {out.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
