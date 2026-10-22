#!/usr/bin/env python3
"""Diagnostic preview PNG (400 m max-pooled): session candidate vs catalogue vs h33.

Pure numpy + zlib PNG encoder (no PIL in the lockfile).  This image is a
sanity-view for humans; it is NOT a validation gate (approval is
src/gems85/submission.py::validate on the written bytes).
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
NEW = ROOT / "docs/downloads/gems85-s85-ctxfus50-37654dots-sep4-20261022T232600Z-4f38c2b3-zeros.tif"
H33 = ROOT / "data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
OUT = ROOT / "docs/downloads/preview_ctxfus50_vs_h33_catalogue.png"


def write_png(path: Path, rgb: np.ndarray) -> None:
    h, w, _ = rgb.shape

    def chunk(t: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + t + data
                + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF))

    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    path.write_bytes(png)


def read(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return np.nan_to_num(s.read(1).astype(np.float32), nan=0.0)


def main() -> int:
    new = read(NEW) > 0
    cat = read(ROOT / "data/labels.tif") == 1
    h33 = read(H33) > 0
    with rasterio.open(ROOT / "data/sample_submission.tif") as s:
        fp = np.isfinite(s.read(1))
    f = 4
    H, W = new.shape
    Hh, Ww = H // f, W // f

    def pool(a):
        return a[:Hh * f, :Ww * f].reshape(Hh, f, Ww, f).max(axis=(1, 3))

    img = np.full((Hh, Ww, 3), 18, np.uint8)
    img[pool(fp)] = (38, 44, 54)
    img[pool(cat)] = (110, 110, 110)     # catalogue
    img[pool(h33)] = (240, 170, 40)      # h33 amber
    img[pool(new)] = (60, 200, 255)      # candidate cyan
    img[pool(new) & pool(h33)] = (120, 255, 140)
    write_png(OUT, img)
    print(f"wrote {OUT.relative_to(ROOT)} {img.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
