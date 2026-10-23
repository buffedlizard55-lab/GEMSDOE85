#!/usr/bin/env python3
"""Automated zero-broken-link and artifact consistency verifier across root & docs/ pages."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for k, v in attrs:
            if k in ("href", "src") and v:
                self.refs.append(v)


def check(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    html_files = [
        root / "index.html",
        root / "docs" / "index.html",
        root / "docs" / "executive-summary.html",
        root / "docs" / "research.html",
        root / "docs" / "methodology.html",
        root / "docs" / "validation.html",
    ]
    for hf in html_files:
        if not hf.is_file():
            problems.append(f"Missing expected HTML page: {hf}")
            continue
        parser = _LinkCollector()
        parser.feed(hf.read_text(encoding="utf-8"))
        for ref in parser.refs:
            parsed = urlparse(ref)
            if parsed.scheme in ("http", "https", "mailto", "javascript", "data"):
                continue
            rel = parsed.path
            if not rel:
                continue
            target = (hf.parent / rel).resolve()
            if not target.exists():
                problems.append(f"{hf.relative_to(root)} -> missing local target '{rel}' ({target})")
    return problems


if __name__ == "__main__":
    errs = check()
    if errs:
        for e in errs:
            print("ERROR:", e)
        raise SystemExit(1)
    print("Link & asset verification PASS: 0 broken links across all 6 HTML entrypoints!")
