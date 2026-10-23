#!/usr/bin/env python3
"""Offline checks for the fail-closed public status site.

This release state has no approved candidate. The checker therefore rejects any
GeoTIFF/ZIP published under docs/, any submission download link, stale positive
banner, or machine record that claims a current file is safe to submit.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIRECT_RASTER_URL = re.compile(r"""https?://[^\s"'<>]*\.(?:tif|tiff|zip)(?:[?#][^\s"'<>]*)?""", re.IGNORECASE)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for name in ("href", "src"):
            if attrs.get(name):
                self.links.append(attrs[name])


def _load(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def check(root: Path = ROOT) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    docs = root / "docs"
    html_files = [root / "index.html", *sorted(docs.rglob("*.html"))]

    for file in html_files:
        if not file.is_file():
            errors.append(f"Missing site page: {file.relative_to(root)}")
            continue
        parser = Links()
        try:
            text = file.read_text(encoding="utf-8")
            parser.feed(text)
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Cannot read HTML {file.relative_to(root)}: {exc}")
            continue

        lowered = text.lower()
        for phrase in (
            "all 17 checks pass — ok to download and submit",
            "ready to submit",
            "submit this",
            "submission file — ready to upload",
        ):
            if phrase in lowered:
                errors.append(f"{file.relative_to(root)}: contains stale positive release text: {phrase}")

        for url in parser.links:
            part = urlsplit(url)
            suffix = Path(unquote(part.path)).suffix.lower()
            if suffix in {".tif", ".tiff", ".zip"}:
                errors.append(f"{file.relative_to(root)}: submission/archive download link is forbidden while blocked: {url}")
            if part.scheme or part.netloc:
                continue
            dest = (file.parent / unquote(part.path)).resolve() if part.path else file
            if not dest.is_relative_to(root.resolve()):
                errors.append(f"{file.relative_to(root)}: link escapes project: {url}")
            elif not dest.exists():
                errors.append(f"{file.relative_to(root)}: broken link: {url}")
            elif part.fragment and dest.suffix.lower() == ".html":
                target = Links()
                try:
                    target.feed(dest.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError) as exc:
                    errors.append(f"Cannot read fragment target {dest.relative_to(root)}: {exc}")
                    continue
                if unquote(part.fragment) not in target.ids:
                    errors.append(f"{file.relative_to(root)}: missing fragment: {url}")

    # No machine-readable or Markdown page may expose a direct prior-raster URL either.
    for path in docs.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".json", ".md", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"Cannot inspect public text file {path.relative_to(root)}: {exc}")
            continue
        for match in DIRECT_RASTER_URL.finditer(text):
            errors.append(f"{path.relative_to(root)}: direct raster/archive URL is forbidden while blocked: {match.group(0)}")

    # A blocked public Pages tree must not publish historic or test rasters as files.
    for suffix in ("*.tif", "*.tiff", "*.zip"):
        for path in docs.rglob(suffix):
            errors.append(f"Blocked Pages tree contains a raster/archive file: {path.relative_to(root)}")

    for relative in ("docs/index.html", "docs/executive-summary.html"):
        path = root / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for required in ("DO NOT DOWNLOAD OR SUBMIT", "No new competition submission GeoTIFF"):
                if required not in text:
                    errors.append(f"{relative}: missing explicit blocked status: {required}")

    card = _load(root / "evidence/run_card.json")
    if not card:
        errors.append("Missing or invalid evidence/run_card.json")
    else:
        if card.get("verdict") != "negative":
            errors.append("Current run card must have verdict=negative while no candidate is cleared")
        if card.get("safe_to_download") is not False or card.get("safe_to_submit") is not False:
            errors.append("Current run card must explicitly set safe_to_download=false and safe_to_submit=false")
        if card.get("raster_sha256") is not None or card.get("submission_name") is not None:
            errors.append("Blocked run card must not identify a current candidate raster/name")
        if card.get("budget", {}).get("experiments_run") != 0:
            errors.append("Current preflight must not claim an experiment was run")
        if card.get("budget", {}).get("experiment_limit") != 3:
            errors.append("Current preflight must preserve the three-experiment limit")
        if card.get("budget", {}).get("hours_used") != 0 or card.get("budget", {}).get("hours_limit") != 2:
            errors.append("Current preflight must preserve the two-hour stop rule with zero time used")
        if card.get("budget", {}).get("submission_slots_used") != 0:
            errors.append("Current preflight must not claim a competition slot was used")
        if card.get("holdout_dti", {}).get("value") is not None or card.get("holdout_dti", {}).get("ci95") is not None:
            errors.append("Current blocked run card must not publish a candidate HOLDOUT-DTI value or CI")
        saturation = card.get("correlation_overlap_vs_registry", {}).get("saturation_certificate", {})
        if saturation.get("witness_path_mismatch") is not True or saturation.get("local_revalidation") is not False:
            errors.append("Current preflight must disclose the saturation-witness path mismatch and lack of local revalidation")
        note = str(card.get("submission_note", ""))
        if len(note) > 140:
            errors.append(f"Blocked run-card note exceeds 140 characters: {len(note)}")

    sub = _load(root / "registry/submission.json")
    if not sub:
        errors.append("Missing or invalid registry/submission.json")
    else:
        if sub.get("status") != "blocked" or sub.get("primary") is not None:
            errors.append("registry/submission.json must be blocked with primary=null")
        if sub.get("safe_to_download") is not False or sub.get("safe_to_submit") is not False:
            errors.append("registry/submission.json must explicitly disallow download/submission")

    lane = _load(root / "registry/lane.json") or {}
    if lane.get("status") != "unassigned":
        errors.append("Expected lane status to remain unassigned; no lane was authorized in this session")
    cache = _load(root / "registry/cache_manifest.json") or {}
    if cache.get("status") != "unavailable" or cache.get("cache_files"):
        errors.append("Expected transformed feature-cache manifest to remain unavailable/empty")
    saturation = _load(root / "evidence/saturation_certificate.json") or {}
    if saturation.get("universal_overlap_blocker") is not True:
        errors.append("Binding literal saturation certificate is missing or no longer records its universal blocker")

    for published, canonical in (
        ("docs/evidence/run_card.json", "evidence/run_card.json"),
        ("docs/registry/submission.json", "registry/submission.json"),
        ("docs/registry/lane.json", "registry/lane.json"),
        ("docs/registry/cache_manifest.json", "registry/cache_manifest.json"),
    ):
        pub, src = root / published, root / canonical
        if not pub.is_file() or not src.is_file() or pub.read_bytes() != src.read_bytes():
            errors.append(f"Published machine record is stale or missing: {published}")

    return errors


if __name__ == "__main__":
    failures = check(ROOT)
    for failure in failures:
        print(failure)
    if failures:
        raise SystemExit(1)
    print("Site safety checks PASS: blocked status is explicit; no raster/ZIP download or positive release claim is published.")
