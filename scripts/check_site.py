#!/usr/bin/env python3
"""Programmatic audit of GitHub Pages HTML, internal links, evidence parity,
and physical GeoTIFF / ZIP submission integrity with zero human inspection.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        for name in ("href", "src"):
            val = d.get(name)
            if val:
                self.links.append(val)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    # 1. Verify internal HTML links & anchors across root index.html + docs/*.html
    html_files = [root / "index.html", *sorted((root / "docs").rglob("*.html"))]
    for file in html_files:
        if not file.is_file():
            errors.append(f"Missing HTML file: {file}")
            continue
        parser = Links()
        parser.feed(file.read_text())
        for url in parser.links:
            part = urlsplit(url)
            if part.scheme or part.netloc:
                continue
            dest = (file.parent / unquote(part.path)).resolve() if part.path else file
            if not dest.is_relative_to(root.resolve()):
                errors.append(f"{file}: link escapes project: {url}")
            elif not dest.exists():
                errors.append(f"{file}: broken link: {url}")
            elif part.fragment and dest.suffix == ".html":
                target = Links()
                target.feed(dest.read_text())
                if unquote(part.fragment) not in target.ids:
                    errors.append(f"{file}: missing fragment: {url}")

    # 2. Verify zero unresolved git conflict markers across tracked text files
    for pat in ("*.md", "*.py", "*.html", "*.json"):
        for p in root.rglob(pat):
            if any(seg in p.parts for seg in (".venv", "data", ".git")):
                continue
            txt = p.read_text(errors="ignore")
            if ("\n" + "<" * 7 + " ") in txt or ("\n" + ">" * 7 + " ") in txt:
                errors.append(f"Unresolved git conflict marker in {p}")

    # 3. Verify byte-for-byte evidence & registry mirror synchronization
    for src in (root / "evidence").glob("*.json"):
        mir = root / "docs" / "evidence" / src.name
        if not mir.is_file() or mir.read_bytes() != src.read_bytes():
            errors.append(f"Stale or missing evidence mirror: {mir}")
    for src in (root / "registry").glob("*.json"):
        mir = root / "docs" / "registry" / src.name
        if not mir.is_file() or mir.read_bytes() != src.read_bytes():
            errors.append(f"Stale or missing registry mirror: {mir}")

    # 4. Programmatically verify Run Card, Uniqueness, Canaries, and GeoTIFF / ZIP bytes
    card = json.loads((root / "evidence" / "run_card.json").read_text())
    if len(card.get("note", "")) > 140 or not card.get("note"):
        errors.append("Submission note missing or exceeds 140 characters")
    if card["leakage_canary"]["max_single_feature_auc"] > 0.90:
        errors.append("Single-feature holdout AUC exceeds 0.90 leakage gate")
    rc = card["registry_comparison"]
    if rc["surface_max_abs_rank_corr_all"] > 0.90 or rc["dots_max_abs_rank_corr_all"] > 0.90:
        errors.append("Spearman rank correlation exceeds 0.90 uniqueness gate")
    if rc["discriminating_max_3px_overlap"] > 0.70 or rc["discriminating_duplicates_count"] != 0:
        errors.append("3-px forward dot overlap exceeds 0.70 across non-saturating fault rasters")

    tif_path = root / card["download_tif"]
    zip_path = root / card["download_zip"]
    if not tif_path.is_file():
        errors.append(f"Missing promoted GeoTIFF: {tif_path}")
    else:
        if _sha256(tif_path) != card["raster_sha256"]:
            errors.append("GeoTIFF SHA-256 mismatch vs run_card.json")
        with rasterio.open(tif_path) as ds:
            arr = ds.read(1)
            if ds.count != 1:
                errors.append(f"Expected 1 band, got {ds.count}")
            if ds.shape != (3730, 3292):
                errors.append(f"Expected shape (3730, 3292), got {ds.shape}")
            if str(ds.crs) != "EPSG:32611":
                errors.append(f"Expected EPSG:32611, got {ds.crs}")
            if ds.dtypes[0] != "float32":
                errors.append(f"Expected float32, got {ds.dtypes[0]}")
            if ds.nodata is not None:
                errors.append(f"Expected nodata=None for all-finite [0,1] raster, got {ds.nodata}")
            if not np.isfinite(arr).all():
                errors.append("Non-finite NaN/Inf values detected in GeoTIFF")
            if float(arr.min()) < 0.0 or float(arr.max()) > 1.0:
                errors.append("GeoTIFF values out of [0, 1] range")
            if int((arr > 0).sum()) != card["emitted_positive_pixels"]:
                errors.append("Positive pixel count mismatch vs run_card.json")

    if not zip_path.is_file():
        errors.append(f"Missing promoted ZIP archive: {zip_path}")
    else:
        if _sha256(zip_path) != card["zip_sha256"]:
            errors.append("ZIP SHA-256 mismatch vs run_card.json")
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            if tif_path.name not in names:
                errors.append(f"ZIP missing {tif_path.name}")
            elif hashlib.sha256(zf.read(tif_path.name)).hexdigest() != card["raster_sha256"]:
                errors.append("Inner GeoTIFF inside ZIP does not match SHA-256")

    # 5. Verify top-of-page download visibility & strict score labels on index and executive-summary
    for page_path in (root / "index.html", root / "docs" / "index.html", root / "docs" / "executive-summary.html"):
        content = page_path.read_text()
        if "SAFE TO DOWNLOAD" not in content or "gemsdoe85-hjcd-ventbridge-submod-zeros.tif" not in content:
            errors.append(f"Missing prominent top download button/status in {page_path}")
        if "HOLDOUT-DTI" not in content:
            errors.append(f"Missing explicit HOLDOUT-DTI label in {page_path}")

    return errors


if __name__ == "__main__":
    errs = check()
    for err in errs:
        print(err)
    if errs:
        raise SystemExit(1)
    print("Site & Submission OK: all HTML links, JSON mirrors, canaries, uniqueness gates, and GeoTIFF/ZIP bytes verified.")
