"""Path resolution for GEMSDOE85 data, caches, evidence, and deliverables."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
BRIDGE_DIR = DATA_DIR / "bridge"
EXTERNAL_REPO_DIR = DATA_DIR / "external"
EVIDENCE_DIR = ROOT / "evidence"
DOCS_DIR = ROOT / "docs"
DOWNLOADS_DIR = DOCS_DIR / "downloads"
DOCS_EVIDENCE_DIR = DOCS_DIR / "evidence"
DOCS_FIGURES_DIR = DOCS_DIR / "figures"
REGISTRY_DIR = ROOT / "registry"


def resolve_raw_dir(preferred: str | Path | None = None) -> Path:
    """Resolve directory holding full restored competition & external rasters."""
    candidates = []
    if preferred is not None:
        candidates.append(Path(preferred))
    env_dir = os.environ.get("GEMS_DATA_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.extend([
        DATA_DIR / "raw",
        Path("/tmp/gems_raw"),
    ])
    for c in candidates:
        if (c / "training_features.tif").exists():
            return c
    return DATA_DIR / "raw"


def resolve_work_dir() -> Path:
    """Scratch directory for memory-mapped float32 matrices (outside git snapshot)."""
    p = Path(os.environ.get("GEMS_WORK_DIR", "/tmp/gems85_work"))
    p.mkdir(parents=True, exist_ok=True)
    return p
