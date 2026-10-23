#!/usr/bin/env python3
"""Fail-closed static-site checks; format PASS is not submission authorization."""
from __future__ import annotations
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = "BLOCKED — DO NOT DOWNLOAD OR SUBMIT"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for name in ("href", "src"):
            if attrs.get(name):
                self.links.append(attrs[name])


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    html_files = [root / "index.html", *sorted((root / "docs").rglob("*.html"))]
    parsed = {}
    for file in html_files:
        parser = Links()
        try:
            parser.feed(file.read_text())
        except Exception as exc:
            errors.append(f"Cannot parse {file}: {exc}")
            continue
        parsed[file] = parser
        for url in parser.links:
            part = urlsplit(url)
            if part.scheme or part.netloc:
                continue
            dest = (file.parent / unquote(part.path)).resolve() if part.path else file
            if not dest.is_relative_to(root.resolve()):
                errors.append(f"{file.relative_to(root)}: link escapes repository: {url}")
            elif not dest.exists():
                errors.append(f"{file.relative_to(root)}: broken local link: {url}")
            elif part.fragment and dest.suffix.lower() == ".html":
                target = Links()
                target.feed(dest.read_text())
                if unquote(part.fragment) not in target.ids:
                    errors.append(f"{file.relative_to(root)}: missing fragment: {url}")

    # Verify the authoritative, fail-closed authorization gates.
    try:
        card = json.loads((root / "evidence/run_card.json").read_text())
        if card.get("verdict") != "negative":
            errors.append("Current run card must remain negative while gates are blocked")
        if card.get("safe_to_download") is not False or card.get("safe_to_submit") is not False:
            errors.append("Current run card must not authorize downloads or submissions")
        if card.get("submission_slots_used") != 0:
            errors.append("Review must not report a submission slot used")
    except Exception as exc:
        errors.append(f"Missing/invalid current evidence/run_card.json: {exc}")

    for page in sorted((root / "docs").rglob("*.html")):
        for href in LinksFor(page).artifact_links():
            errors.append(f"{page.relative_to(root)} exposes historical artifact as a download: {href}")

    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html"):
        p = root / rel
        text = p.read_text() if p.exists() else ""
        if BLOCKED not in text:
            errors.append(f"{rel} must prominently state {BLOCKED}")
        if "ALL 17 CHECKS PASS — OK TO DOWNLOAD AND SUBMIT" in text:
            errors.append(f"{rel} contains a stale submit-ready claim")

    # Published snapshots must not silently retain a stale run card.
    snapshots = {
        "docs/evidence/run_card.json": "evidence/run_card.json",
        "docs/downloads/run_card.json": "evidence/run_card.json",
        "docs/evidence/review_passes.json": "evidence/review_passes.json",
        "docs/registry/irregularities.json": "registry/irregularities.json",
    }
    for published, canonical in snapshots.items():
        p = root / published
        if p.exists() and p.read_bytes() != (root / canonical).read_bytes():
            errors.append(f"Stale published snapshot: {published}")
    return errors


class LinksFor:
    """Extract visible active links to GeoTIFF/ZIP prediction artifacts."""
    def __init__(self, path: Path):
        self.path = path

    def artifact_links(self):
        parser = Links()
        parser.feed(self.path.read_text())
        return [url for url in parser.links
                if (not urlsplit(url).netloc or urlsplit(url).netloc == "raw.githubusercontent.com")
                and urlsplit(url).path.lower().endswith((".tif", ".tiff", ".zip"))
                and ("downloads/" in urlsplit(url).path or "/submissions/" in urlsplit(url).path)]


if __name__ == "__main__":
    errors = check()
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print("Site OK: links resolve; current site and run card fail closed; no active historical TIFF download links on entry pages.")
