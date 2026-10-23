"""Rebuild the incumbent R0 from its pinned parent, then measure ONE axis at a time.

Why this module exists
----------------------
The incumbent ``h33-h33-2-b2`` (owner-claimed live 0.2778) is the fourth rung of a
geometric pruning cascade.  This session's unit of work is *one controlled change from a
named parent*, so three things must be true before any variant exists:

1. the parent is the real parent (bytes pinned, hash verified, never approximated);
2. the parent can be re-derived from that parent by a named rule and shown to be
   pixel-identical to the incumbent;
3. every variant differs from the incumbent *only* on the assigned axis, and the difference
   is counted, not described.

The cascade, verified in this checkout (``evidence/r0_rebuild.json``):

    H19-5 binary support (121,131 px)
      -> greedy minimum-separation 2.8 px placement (44,090 dots)        [d2.8 file]
      -> minus dots with Euclidean d(catalogue) <= 1 px (40,199)          [0.2708, PRUNE=1]
      -> minus dots with Euclidean d(catalogue) <= 2 px (37,654)          [0.2778, PRUNE=2 = R0]

Two independent routes reproduce the incumbent exactly: pruning the d2.8 file at cutoff 2,
and pruning the 40,199-dot parent at cutoff 2.  Both give the same 37,654 pixels, so the
brief's description of R0 and the file's own arithmetic agree.

File bytes are a different matter.  Re-serialising the identical pixel array does **not**
reproduce the incumbent's SHA-256 in this environment (the incumbent used DEFLATE
predictor=3 with a compression stack that is not available here).  That is recorded in
``IRREGULARITIES.md`` as IR-V2-01 and handled by comparing *pixels*, while all parent-diff
statistics are still computed against the pinned incumbent bytes.

Nothing in this module selects a submission, a slot, or a lane.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
BRIDGE = DATA / "bridge"
WORK = ROOT / "work" / "ref"
RELEASES = ROOT / "releases"

#: Pinned parents/grandparents.  ``data_manifest.json`` is the primary pin; the three fleet
#: rasters that the manifest does not carry are pinned by ``registry/scored_artifacts.json``
#: (same hash the repository's own ``scripts/build_registry.py`` verifies).
PINNED = {
    "r0": dict(  # the incumbent: PRUNE=2
        repo="buffedlizard55-lab/GEMSDOE32",
        ref="main",
        path="docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        dest=WORK / "h33-zeros.tif",
        sha256="c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        bytes=219065,
        pin="registry/scored_artifacts.json",
    ),
    "prune1": dict(  # h27-4-solo-d28: PRUNE=1, owner-claimed 0.2708
        repo="buffedlizard55-lab/GEMSDOE31",
        ref="main",
        path="docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        dest=WORK / "h27-4-nan.tif",
        sha256="07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40",
        bytes=199214,
        pin="registry/scored_artifacts.json",
    ),
    "d28": dict(  # d2.8, 44,090 dots: PRUNE=0
        repo="buffedlizard55-lab/GEMSDOE24",
        ref="07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        path="docs/downloads/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        dest=WORK / "d28-nan.tif",
        sha256="91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8",
        bytes=1603424,
        pin="registry/data_manifest.json#scored_d28_unscored",
    ),
    "h19_5": dict(  # the binary field every dot in the cascade sits on
        repo="buffedlizard55-lab/GEMSDOE24",
        ref="07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        path="inputs/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        dest=WORK / "h19-5-nan.tif",
        sha256="ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
        bytes=1712322,
        pin="registry/data_manifest.json#scored_h19_5",
    ),
}

ALPHA = 0.2
BETA = 0.8
R_PX = 3.0


# --------------------------------------------------------------------------------------- pins
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_pinned(key: str, *, offline_ok: bool = True) -> Path:
    """Materialise a pinned raster, verifying its SHA-256 before it is used.

    Fetches through the authenticated ``gh`` CLI (GitHub is an allowed host).  A file that
    is already present is accepted only if its bytes match the pin.
    """
    entry = PINNED[key]
    dest = Path(entry["dest"])
    if dest.is_file():
        if sha256_file(dest) != entry["sha256"]:
            raise ValueError(f"{key}: cached file {dest} does not match its pin; refusing to use it")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with tmp.open("wb") as out:
        subprocess.run(
            ["gh", "api", f"repos/{entry['repo']}/contents/{entry['path']}?ref={entry['ref']}",
             "-H", "Accept: application/vnd.github.raw"],
            stdout=out, check=True, timeout=600,
        )
    got = sha256_file(tmp)
    if got != entry["sha256"]:
        tmp.unlink(missing_ok=True)
        raise ValueError(f"{key}: fetched {got} != pinned {entry['sha256']}")
    tmp.replace(dest)
    return dest


# ----------------------------------------------------------------------------------- the grid
def load_template():
    """Footprint + catalogue from the two bridge files, hash-checked against vendor pins."""
    from gems57 import grid as _grid  # vendored, unmodified

    if sha256_file(BRIDGE / "sample_submission.tif") != _grid.SHA256_SAMPLE_SUBMISSION:
        raise ValueError("sample_submission.tif does not match its pin")
    if sha256_file(BRIDGE / "existing_faults.tif") != _grid.SHA256_EXISTING_FAULTS:
        raise ValueError("existing_faults.tif does not match its pin")
    g = _grid.load_grid(BRIDGE)
    return g.footprint, g.catalogue


def read_dots(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    a = np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0)
    return a > 0


def catalogue_distance(catalogue: np.ndarray) -> np.ndarray:
    """Euclidean distance in pixels from every cell to the nearest mapped-fault cell.

    Euclidean, not Chebyshev: a cutoff of 3 px must mean the metric's own R = 300 m.
    Measured difference on this grid: Chebyshev-2 removal keeps 36,043 of the 40,199 dots
    and does *not* reproduce the incumbent; Euclidean-2 keeps 37,654 and does.
    """
    return ndi.distance_transform_edt(~np.asarray(catalogue, bool))


# ------------------------------------------------------------------------------- the rebuild
def prune(dots: np.ndarray, dist: np.ndarray, cutoff: float) -> np.ndarray:
    """The cascade's only edit: delete dots within ``cutoff`` px of the catalogue."""
    return np.asarray(dots, bool) & ~(dist <= cutoff)


@dataclass(frozen=True)
class Rebuild:
    dots: np.ndarray
    n_dots: int
    pixel_identical_to_pinned: bool
    n_differing_pixels: int

    def as_dict(self, **extra) -> dict:
        d = dict(n_dots=int(self.n_dots),
                 pixel_identical_to_pinned=bool(self.pixel_identical_to_pinned),
                 n_differing_pixels=int(self.n_differing_pixels))
        d.update(extra)
        return d


def rebuild_r0(cutoff: float = 2.0, *, parent: str = "d28") -> Rebuild:
    """Re-derive the incumbent from a pinned parent and check pixel identity."""
    fp, cat = load_template()
    dist = catalogue_distance(cat)
    dots = prune(read_dots(fetch_pinned(parent)), dist, cutoff)
    dots &= fp
    inc = read_dots(fetch_pinned("r0"))
    diff = int((dots ^ inc).sum())
    return Rebuild(dots=dots, n_dots=int(dots.sum()),
                   pixel_identical_to_pinned=diff == 0, n_differing_pixels=diff)


# ----------------------------------------------------------------------------- diff statistics
def diff_stats(parent: np.ndarray, child: np.ndarray) -> dict:
    p, c = np.asarray(parent, bool), np.asarray(child, bool)
    n_p, n_c = int(p.sum()), int(c.sum())
    added = int((c & ~p).sum())
    removed = int((p & ~c).sum())
    common = int((p & c).sum())
    changed = added + removed
    return dict(
        n_parent=n_p, n_child=n_c, n_added=added, n_removed=removed, n_common=common,
        n_changed=changed,
        pct_of_parent_dots_changed=round(100.0 * changed / n_p, 4) if n_p else None,
        pct_mass_added=round(100.0 * added / n_p, 4) if n_p else None,
        jaccard=round(common / (n_p + n_c - common), 6) if (n_p + n_c - common) else None,
    )


# ------------------------------------------------------------------------------- serialisation
_TIFF_PROFILE = dict(driver="GTiff", count=1, dtype="float32",
                     tiled=True, blockxsize=256, blockysize=256,
                     compress="deflate", predictor=2)


def write_zeros(path: Path, dots: np.ndarray) -> None:
    """All-finite 0/1 raster: the fallback the operator uploads."""
    arr = np.asarray(dots, bool).astype(np.float32)
    with rasterio.open(BRIDGE / "sample_submission.tif") as ref:
        prof = dict(_TIFF_PROFILE, height=ref.height, width=ref.width,
                    crs=ref.crs, transform=ref.transform)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr, 1)


def write_nan(path: Path, dots: np.ndarray, footprint: np.ndarray) -> None:
    """NaN outside the scored footprint, 0 inside it, 1 on a dot: the primary format."""
    arr = np.asarray(dots, bool).astype(np.float32)
    arr[~np.asarray(footprint, bool)] = np.nan
    with rasterio.open(BRIDGE / "sample_submission.tif") as ref:
        prof = dict(_TIFF_PROFILE, height=ref.height, width=ref.width,
                    crs=ref.crs, transform=ref.transform, nodata=float("nan"))
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr, 1)


# ------------------------------------------------------------------------------------- gates
def gates(path: Path, footprint: np.ndarray, catalogue: np.ndarray, *,
          mode: str = "nan", dist: np.ndarray | None = None,
          min_catalogue_px: float = 3.0) -> dict:
    """The brief's MUST-pass set, evaluated from the bytes on disk (§6)."""
    problems: list[str] = []
    with rasterio.open(path) as src, rasterio.open(BRIDGE / "sample_submission.tif") as ref:
        a = src.read(1)
        info = dict(path=str(path.relative_to(ROOT)) if str(path).startswith(str(ROOT)) else str(path),
                    sha256=sha256_file(path), bytes=Path(path).stat().st_size,
                    bands=src.count, dtype=src.dtypes[0], crs=str(src.crs),
                    shape=[src.height, src.width], nodata=src.nodata,
                    transform=[float(v) for v in tuple(src.transform)[:6]])
        if src.count != 1:
            problems.append(f"{src.count} bands")
        if src.dtypes[0] != "float32":
            problems.append(f"dtype {src.dtypes[0]}")
        if (src.height, src.width) != (ref.height, ref.width):
            problems.append("shape differs from sample_submission")
        if src.crs != ref.crs:
            problems.append("CRS differs from sample_submission")
        if src.transform != ref.transform:
            problems.append("transform differs from sample_submission")
        info["ref_transform"] = [float(v) for v in tuple(ref.transform)[:6]]
        if info["transform"] != info["ref_transform"]:
            problems.append("transform (6) differs from sample_submission")
    fp = np.asarray(footprint, bool)
    inside = a[fp]
    outside = a[~fp]
    n_nan_inside = int(np.isnan(inside).sum() + np.isinf(inside).sum())
    n_nan_outside = int(np.isnan(outside).sum())
    finite_outside = outside[np.isfinite(outside)]
    zeros_outside = bool(finite_outside.size == 0 or np.all(finite_outside == 0.0))
    if mode not in {"nan", "zeros"}:
        problems.append(f"unknown mode {mode!r}")
    if n_nan_inside:
        problems.append(f"{n_nan_inside} NaN/inf cells inside the footprint")
    if mode == "nan" and n_nan_outside != int(outside.size):
        problems.append(f"{int(outside.size) - n_nan_outside} outside-footprint cells are not NaN")
    if mode == "zeros":
        if n_nan_outside:
            problems.append(f"{n_nan_outside} outside-footprint cells are NaN in zeros mode")
        if not zeros_outside:
            problems.append(f"{int((finite_outside != 0).sum())} non-zero cells outside the footprint")
    if inside.size and (inside.min() < 0 or inside.max() > 1):
        problems.append(f"values outside [0,1]: {inside.min()}..{inside.max()}")
    if not np.isin(np.unique(inside), [0.0, 1.0]).all():
        problems.append("inside-footprint values are not binary 0/1")
    mass_inside = float(np.nansum(inside))
    on_cat = int((np.nan_to_num(a, nan=0.0) > 0)[np.asarray(catalogue, bool)].sum())
    if on_cat:
        problems.append(f"{on_cat} dots on catalogue pixels")
    info.update(nan_inside_footprint=n_nan_inside,
                nan_outside_footprint=n_nan_outside,
                finite_outside_footprint=int(finite_outside.size),
                zeros_outside_footprint=zeros_outside,
                min_inside=float(inside.min()) if inside.size else None,
                max_inside=float(inside.max()) if inside.size else None,
                mass_inside=mass_inside,
                dots_on_catalogue=on_cat)
    if dist is not None:
        d = np.broadcast_to(dist, a.shape)[np.nan_to_num(a, nan=0.0) > 0]
        info["min_distance_to_catalogue_px"] = float(d.min()) if d.size else None
        info["n_dots_inside_3px"] = int((d < min_catalogue_px).sum())
        if d.size and float(d.min()) < min_catalogue_px:
            problems.append(f"{int((d < min_catalogue_px).sum())} dots closer than {min_catalogue_px} px to the catalogue")
    info.update(mode=mode, problems=problems, ok=not problems)
    return info


# --------------------------------------------------------------------------------- DTI algebra
def kernel_offsets(r: float = R_PX) -> list[tuple[int, int, float]]:
    out = []
    for dy in range(-int(np.floor(r)), int(np.floor(r)) + 1):
        for dx in range(-int(np.floor(r)), int(np.floor(r)) + 1):
            d = float(np.hypot(dy, dx))
            if d <= r:                      # d == 0 (a dot exactly on truth) has k = 1
                out.append((dy, dx, 1.0 - d / r))
    return out


OFFSETS = kernel_offsets()


def kernel_max(a: np.ndarray, offsets=OFFSETS) -> np.ndarray:
    """max_{delta} a(x+delta) k(|delta|) -- exact grey-scale dilation, zero outside."""
    a = np.asarray(a, dtype=np.float64)
    h, w = a.shape
    out = np.zeros_like(a)
    for dy, dx, k in offsets:
        ys_src = slice(max(0, -dy), h - max(0, dy))
        ys_dst = slice(max(0, dy), h - max(0, -dy))
        xs_src = slice(max(0, -dx), w - max(0, dx))
        xs_dst = slice(max(0, dx), w - max(0, -dx))
        np.maximum(out[ys_dst, xs_dst], a[ys_src, xs_src] * k, out=out[ys_dst, xs_dst])
    return out


def dti(pred: np.ndarray, truth: np.ndarray, alpha: float = ALPHA, beta: float = BETA) -> dict:
    """DTI = T / (alpha*T + alpha*(S-M) + beta*|G|), the brief's verified algebra."""
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, bool)
    credit_at_truth = kernel_max(p)          # T(x) = max_delta p(x+delta) k(delta)
    T = float(credit_at_truth[g].sum())
    S = float(p.sum())
    # M = sum_x p(x) * max_g k(d(x,g)): the dilation runs from truth out to the prediction,
    # which is why it is kernel_max(truth), not kernel_max(prediction).
    M = float((p * kernel_max(g)).sum())
    nG = int(g.sum())
    den = alpha * T + alpha * (S - M) + beta * nG
    return dict(dti=T / den if den else 0.0, T=T, S=S, M=M, n_truth=nG, den=den)


def marginal_gain(pred: np.ndarray, truth: np.ndarray, y: int, x: int,
                  alpha: float = ALPHA) -> float:
    """Exact change in DTI from adding one unit of mass at (y, x)."""
    base = dti(pred, truth, alpha=alpha)
    p2 = pred.copy()
    p2[y, x] = 1.0
    return float(dti(p2, truth, alpha=alpha)["dti"] - base["dti"])


def catalogue_proxy_dti(pred: np.ndarray) -> dict:
    """PROXY ONLY: score against the *published* catalogue.

    Useless as a performance estimate for R0-like files (they are built to emit zero mass on
    that catalogue, so the proxy punishes them for the exclusions and rewards flanking), but
    it is the only truth raster in the checkout and it is reported as PROXY, never a score.
    """
    fp, cat = load_template()
    return dti(np.where(fp, np.asarray(pred, np.float64), 0.0), cat)


def release_record(release_id: str, parent_id: str, axis: str, value: str,
                   dots: np.ndarray, *, note: str = "", extra: dict | None = None) -> dict:
    return dict(id=release_id, parent=parent_id, axis=axis, value=value,
                n_dots=int(np.asarray(dots, bool).sum()), note=note[:140],
                **(extra or {}))


def write_json(path: Path, obj: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
