#!/usr/bin/env python3
"""Offline internal-link, evidence-integrity, GeoTIFF SHA-256, and top-of-site readiness checks."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(str(d["id"]))
        for name in ("href", "src"):
            if d.get(name):
                self.links.append(str(d[name]))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    files = [root / "index.html", *sorted((root / "docs").rglob("*.html"))]
    for file in files:
        if not file.exists():
            errors.append(f"Missing required HTML file: {file}")
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

    # Byte-exact mirror sync between evidence/ & docs/evidence/ and registry/ & docs/registry/
    for source in sorted((root / "docs" / "evidence").glob("*.json")):
        original = root / "evidence" / source.name
        if not original.exists() or source.read_bytes() != original.read_bytes():
            errors.append(f"Stale/altered published evidence: {source}")
    for source in sorted((root / "docs" / "registry").glob("*.json")):
        original = root / "registry" / source.name
        if not original.exists() or source.read_bytes() != original.read_bytes():
            errors.append(f"Stale/altered published registry: {source}")

    # Every public GeoTIFF under docs/downloads/ must have an accompanying automated check/audit JSON
    for tif in sorted((root / "docs" / "downloads").glob("*.tif")):
        sidecar_checks = Path(str(tif) + ".checks.json")
        stem_base = tif.stem.removesuffix("-zeros").removesuffix("-nan")
        sidecar_audit = tif.parent / f"{stem_base}-audit.json"
        if not sidecar_checks.exists() and not sidecar_audit.exists():
            errors.append(f"Unvalidated GeoTIFF in docs/downloads/ lacking checks/audit JSON: {tif}")

    card = json.loads((root / "docs" / "evidence" / "run_card.json").read_text())
    sub = json.loads((root / "registry" / "submission.json").read_text())

    if card.get("verdict") == "promote":
        if card.get("safe_to_download") is not True or card.get("format_validated_for_upload") is not True:
            errors.append("Promoted run card must explicitly certify safe_to_download and format_validated_for_upload")
        if not card.get("leakage_canary", {}).get("passed"):
            errors.append("Promoted run card failed leakage canary")
        vo = card.get("validator_output", {})
        if not (vo.get("gems57_template_ok") and vo.get("gems85_zeros_passed")):
            errors.append("Promoted run card failed automated GeoTIFF validators")
        uq = card.get("correlation_vs_registry", {})
        if not uq.get("pre_placement_surface_passed_le_090") or uq.get("discriminating_overlap_firings", 1) != 0:
            errors.append("Promoted run card failed uniqueness gate")
        note = sub.get("note", "")
        if not (1 <= len(note) <= 140) or note != card.get("submission_note"):
            errors.append("Submission note missing, >140 chars, or mismatched between submission.json and run_card.json")

        pri_file = root / "docs" / "downloads" / sub["primary"]["filename"]
        if not pri_file.exists():
            errors.append(f"Missing promoted primary GeoTIFF: {pri_file}")
        else:
            got_sha = _sha256(pri_file)
            if got_sha != sub["primary"]["sha256"] or got_sha != card.get("raster_sha256"):
                errors.append("Primary GeoTIFF SHA-256 mismatch against submission.json / run_card.json")

        for html_path in (root / "index.html", root / "docs" / "index.html", root / "docs" / "executive-summary.html"):
            txt = html_path.read_text()
            if "OK TO DOWNLOAD" not in txt or sub["primary"]["filename"] not in txt:
                errors.append(f"Missing unmistakable top-of-site OK TO DOWNLOAD status or filename in {html_path}")
    elif card.get("verdict") == "negative":
        for name in ("index.html", "executive-summary.html"):
            txt = (root / "docs" / name).read_text()
            if "No verified submission TIFF is available" not in txt and "Current decision: do not submit" not in txt:
                errors.append(f"Missing visible blocked status in docs/{name}")
    else:
        errors.append(f"Invalid run_card verdict: {card.get('verdict')}")

    return errors


if __name__ == "__main__":
    errs = check()
    for e in errs:
        print(e)
    if errs:
        raise SystemExit(1)
    print("Site OK: internal links, fragments, synced evidence/registry JSONs, SHA-256 GeoTIFF gates, and readiness banners verified.")
