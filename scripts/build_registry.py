#!/usr/bin/env python3
"""Collect every prior GEMSDOE submission raster we can locate, with its OWNER-REPORTED score.

These rasters serve two purposes and only two:
  (1) the parallel-run protocol's **duplicate check** -- a new candidate may not exceed
      rank-correlation 0.90 with any of them, nor place >70 % of its dots within 3 px of
      one of them;
  (2) **instrument calibration** -- Spearman rho between this repo's holdout DTI and the
      owner-reported live scores, which tells us how much the holdout can be trusted.

Every score here is OWNER-REPORT (copied from the operator's own ledger of submission-page
receipts).  None of them is verified by this repository against a DrivenData receipt page.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = Path("/home/user/ref")
DEST = ROOT / "data" / "registry_rasters"

# (local source, owner-reported live DW-Tversky, label)
# Sources: the operator's brief, which lists one score per published artifact name.
SPEC = [
    # --- the lineage that produced the group's best score ---
    ("ref:GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
     0.2778, "h33-2-b2  (GROUP BEST: 0.2708 base with all dots <=2px from catalogue deleted)"),
    ("ref:GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
     0.2708, "h27-4-solo-d28 (the base h33-2-b2 was pruned from)"),
    ("ref:GEMSDOE30/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
     0.2600, "d28-poisson300m-offcat-44090"),
    ("data:scored_d28_unscored", 0.2600, "dotted-h19-5-d2-8 (44,090 px)"),
    ("data:scored_d15_scored", 0.2477, "dotted-h19-5-d1-5 (60,069 px)"),
    ("data:scored_h19_5", 0.1922, "h19-5 solid powerlaw-budget multiline (121,131 px)"),
    ("data:scored_h19_4", 0.1894, "h19-4 multiline corroborated"),
    ("data:scored_h16_1", 0.1855, "h16-1 topo-geophys baseline ridges"),
    ("data:scored_gems27_tgc_v2_d15", 0.2449, "topo-gap-closure v2 on d1.5"),
    # --- other families, for rank-correlation spread ---
    ("ref:GEMSDOE49/docs/downloads/gems49-gate_ortho_w0.25-40k-20261006T213721Z-zeros.tif",
     0.2376, "gate_ortho w0.25 40k"),
    ("ref:GEMSDOE63/docs/downloads/gemsdoe63-cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros.tif",
     0.2303, "cvarlw-thin s3.17 54,864"),
    ("data:calib_gems10-h28-dotted-ridge-20260928T0202562",
     0.1839, "h28 dotted ridge"),
    ("data:calib_8GEMSDOE_Hedge-v2_submission", 0.1563, "Hedge-v2"),
    ("data:calib_gemsdoe-ens12-adopted-7f00890a", 0.1563, "gems-submission ens12"),
    ("data:calib_gems10-h25-ctx-ridge-20260927T2329477041", 0.1280, "H25 ctx-ridge"),
    ("data:calib_13gems_20261001_r13-lattice-s5_v2_nan-ou", 0.0904, "r13 lattice s5 v2"),
    ("data:calib_gemsdoe9-PLACEHOLDER-2314b599", 0.0107, "gemsdoe9 placeholder"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def resolve(src: str, expected_hashes: dict[str, str] | None = None) -> Path | None:
    if src.startswith("ref:"):
        rel = src[4:]
        p = REF / rel
        if p.exists():
            return p
        # Fallback: fetch from buffedlizard55-lab/<repo> via gh api into DEST and verify SHA-256
        repo_name, repo_path = rel.split("/", 1)
        dst = DEST / Path(repo_path).name
        exp = (expected_hashes or {}).get(dst.name)
        if dst.exists() and (exp is None or sha256(dst) == exp):
            return dst
        import subprocess
        import tempfile
        DEST.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=DEST, delete=False) as tf:
            tmp_path = Path(tf.name)
            res = subprocess.run(
                ["gh", "api", f"repos/buffedlizard55-lab/{repo_name}/contents/{repo_path}",
                 "-H", "Accept: application/vnd.github.raw"],
                stdout=tf, check=False, timeout=180,
            )
        if res.returncode != 0 or not tmp_path.exists() or tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            return None
        if exp is not None and sha256(tmp_path) != exp:
            tmp_path.unlink(missing_ok=True)
            raise ValueError(f"SHA-256 mismatch fetching {src}")
        tmp_path.replace(dst)
        return dst
    if src.startswith("data:"):
        man = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
        for f in man["files"]:
            if f["id"] == src[5:]:
                p = ROOT / "data" / f["dest"]
                return p if p.exists() else None
    return None


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    prev_path = ROOT / "registry" / "scored_artifacts.json"
    expected_hashes = {}
    if prev_path.exists():
        for a in json.loads(prev_path.read_text()).get("artifacts", []):
            expected_hashes[Path(a["file"]).name] = a["sha256"]
    out = []
    missing = []
    for src, score, label in SPEC:
        p = resolve(src, expected_hashes=expected_hashes)
        if p is None:
            missing.append(src)
            continue
        dst = DEST / p.name
        if p.resolve() != dst.resolve() and not dst.exists():
            shutil.copy2(p, dst)
        out.append({
            "file": f"data/registry_rasters/{p.name}",
            "owner_reported_live_dti": score,
            "label": label,
            "source": src,
            "sha256": sha256(dst),
            "bytes": dst.stat().st_size,
            "evidence_class": "OWNER-REPORT (operator ledger; not verified against a DrivenData receipt here)",
        })
        print(f"[ok] {score:.4f}  {p.name}")
    for m in missing:
        print(f"[MISSING] {m}")
    (ROOT / "registry" / "scored_artifacts.json").write_text(
        json.dumps({"note": "Scores are OWNER-REPORT, copied from the operator's brief. "
                            "No DrivenData receipt is reproduced in this repository.",
                    "n": len(out), "missing": missing, "artifacts": out}, indent=2) + "\n")
    print(f"\n{len(out)} registry rasters, {len(missing)} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
