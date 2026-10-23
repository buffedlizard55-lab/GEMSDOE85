"""
GEMSDOE85 Hypotheses — 5 distinct, implementable candidates (no external data).

All hypotheses use ONLY the 19 official training_features bands + the already-provided
catalogue raster. No external downloads required, so every hypothesis is locally
validatable via the spatially-blocked holdout (alpha 0.2 beta 0.8 300 m triangular kernel).

Each hypothesis names:
  - specific layer(s) involved (official band names/band numbers)
  - physical signature (edge-detection / curvature / strain transform)
  - why it should catch a fault MISSING from USGS/INGENIOUS catalogue rather than one already in it
  - how it differs from anything already in GEMSDOE32 (which already implements H33-A..E)

Ranking is by expected DTI improvement per implementation cost.
"""

from __future__ import annotations
import numpy as np
from scipy.ndimage import gaussian_filter, sobel, distance_transform_edt

# Band indices (1-based) as per training_features.tif tags
BAND = {
    "mag_anom": 1,
    "rtp": 2,
    "tmi_hg": 3,
    "geod_2ndinv": 4,
    "iso_grav_anom_slope": 5,
    "tc": 6,
    "geod_shearrate": 7,
    "geod_dilaterate": 8,
    "tmi_vg": 9,
    "deq_n100a15": 10,
    "iso_grav_anom_vg": 11,
    "det_elev": 12,
    "iso_grav_anom": 13,
    "tmi": 14,
    "depth_to_base_surf": 15,
    "ieq_n100a15": 16,
    "cond_surf": 17,
    "iso_grav_anom_hg": 18,
    "det_elev_slope": 19,
}

# Canonical footprint: use sample_submission as template (verified 5_167_373 px)
# Transform: 100,0,243350,0,-100,4508550, EPSG:32611, 3292x3730

HYPOTHESES = [
    {
        "id": "H85-1",
        "title": "Transtensional pull-apart / releasing bend detector from geodetic strain",
        "rank": 1,
        "layers": [
            "geod_dilaterate (8) — rate of volumetric strain, negative = extension",
            "geod_shearrate (7) — angular shear rate",
            "geod_2ndinv (4) — strain rate tensor magnitude",
        ],
        "signature": "Transtensional index TI = ReLU(-dilatation) * shear / (2nd_invariant + eps), smoothed σ=1.5 px, then Hessian ridge response. Physical target: dilational jogs and pull-apart basins where oblique extension creates high permeability for geothermal fluids (Faulds et al. Great Basin model).",
        "why_off_catalogue": "USGS Quaternary catalogue records surface traces, not subsurface kinematics. A pull-apart basin between two en-echelon fault segments has NO through-going surface trace but produces a characteristic negative-dilatation + high-shear strain anomaly. Expert mappers under-map these because the bounding faults may each be <500 m surface expression.",
        "differs": "GEMSDOE32 uses geodetic bands only as scalar features or not at all (13 of 19 bands have zero derived channels). H32 multipysics uses mag/grav/cond/topography but never combines the three geodetic strain bands into a kinematic ratio. No prior arm computes dilation-weighted shear or transtension.",
        "expected_dti": "+0.008 to +0.015 proxy DTI at matched mass (0.26 baseline → 0.268-0.275); cost Very Low (~30 s CPU).",
        "cost": "Very Low (3 bands, 2 filters, 1 ratio)",
        "status": "IMPLEMENTED — primary for GEMSDOE85",
    },
    {
        "id": "H85-2",
        "title": "Gravity worm multiscale edge persistence (density contrast duplex)",
        "rank": 2,
        "layers": [
            "iso_grav_anom (13) — isostatic gravity anomaly",
            "iso_grav_anom_hg (18) — horizontal gradient",
            "iso_grav_anom_vg (11) — vertical gradient",
            "iso_grav_anom_slope (5) — slope of anomaly",
            "depth_to_base_surf (15) — basement depth (corroboration)",
        ],
        "signature": "Multiscale normalized gradient magnitude Gσ = |∇ iso_grav_anom|_σ at σ=1.2,2.5,4.0 px via Gaussian derivative; persistence P = geometric mean of Gσ across scales (worm). Corroborate where depth_to_base_surf gradient orientation agrees within 30°. Targets basement steps under cover.",
        "why_off_catalogue": "Covered basement faults have no surface scarp but produce linear density contrasts. The catalogue is biased to surface-mappable faults; gravity worms image the subsurface contact directly. A persistent worm indicates a through-going basement structure independent of erosion.",
        "differs": "Existing gravity channels are single-scale gradient magnitudes (features.py) — no multiscale persistence, no worm concept, no orientation corroboration with basement depth. LiDAR-centric prior work never touches gravity worms.",
        "expected_dti": "+0.005 to +0.012 proxy; cost Low (~40 s CPU)",
        "cost": "Low",
        "status": "REGISTERED — not yet built; shares implementation with H85-1 as secondary arm in duplex",
    },
    {
        "id": "H85-3",
        "title": "Magnetic tilt-depth + analytic signal duplex (buried contact lineament)",
        "rank": 3,
        "layers": [
            "tc (6) — tilt / total curvature (edge detector)",
            "tmi_hg (3) — TMI horizontal gradient",
            "tmi_vg (9) — TMI vertical gradient",
            "tmi (14) — total magnetic intensity",
            "rtp (2) — reduced-to-pole",
            "mag_anom (1) — magnetic anomaly",
        ],
        "signature": "Analytic signal AS = sqrt(tmi_hg² + tmi_vg² + rtp_vg² approx); tilt zero-contour extraction (tc = 0 marks contact edge); product field = AS * exp(-|tc|/0.5) * coherence_of_tmi_hg_direction. Detects buried magnetic contacts (faulted basement/volcanic).",
        "why_off_catalogue": "Magnetics see basement lithology contacts that may be fault-juxtaposed but have no topographic expression. The catalogue is dominated by range-front normal faults; intrabasin buried faults (Walker Lane transtension) are systematically absent but magnetic-lineament rich.",
        "differs": "GEMSDOE32 has per-band ridge responses and gradient magnitudes but never computes analytic signal or tilt-depth combination, and never uses orientation coherence of magnetic gradients. H33-A uses orientation order parameter across physics, not within magnetics duplex.",
        "expected_dti": "+0.003 to +0.009; cost Medium (~50 s)",
        "cost": "Medium",
        "status": "REGISTERED",
    },
    {
        "id": "H85-4",
        "title": "Relay-ramp / soft-linkage topographic corridor from detrended elevation curvature",
        "rank": 4,
        "layers": [
            "det_elev (12) — detrended elevation",
            "det_elev_slope (19) — detrended slope",
            "depth_to_base_surf (15) — basement depth as anti-correlation check",
        ],
        "signature": "Profile curvature (second derivative along slope direction) + plan curvature (across slope) from det_elev; corridor = low-relief (det_elev_slope < p30) + relay-like curvature signature (adjacent positive/negative curvature pair = ramp between overlapping faults). Morphometric, not just ridge.",
        "why_off_catalogue": "Relay ramps form between overlapping normal fault segments; by definition at least one segment tip is beyond the mapped trace end. Topographic relay ramps are subtle (few meters relief) and omitted from air-photo catalogue; det_elev removes regional tilt to reveal them.",
        "differs": "Existing DEM channels are ridge NMS, relief5, tophat2 — all local. None compute profile/plan curvature pair or ramp topology. H33-B uses valley chaining, not curvature ramps.",
        "expected_dti": "+0.002 to +0.006; cost Low (~35 s)",
        "cost": "Low",
        "status": "REGISTERED",
    },
    {
        "id": "H85-5",
        "title": "Conductive clay-cap edge + depth-to-basement step joint (MT-imaged geothermal seal)",
        "rank": 5,
        "layers": [
            "cond_surf (17) — surface conductivity (MT proxy)",
            "depth_to_base_surf (15) — basement depth",
            "geod_2ndinv (4) — strain as corroboration for active vs inactive",
        ],
        "signature": "Conductivity step: gradient mag of cond_surf × directional coherence (3×3 window cosine similarity of gradient direction) = straight conductive boundary (clay cap edge over fault). Joint with basement step gradient alignment; retain only where 2nd invariant > p50 (active strain).",
        "why_off_catalogue": "MT conductivity images clay alteration above geothermal reservoirs (the clay cap). Its edge marks the bounding fault permeability pathway. Surface catalogue cannot see alteration; geophysics does. Joint with basement step ensures the step is structural not lithologic.",
        "differs": "cond_surf and depth_to_base appear only as scalars / plain gradients in features.py. No prior hypothesis requires gradient directional coherence (straight boundary) nor active-strain gating. H33-D uses cond+depth but without coherence or strain corroboration.",
        "expected_dti": "+0.002 to +0.008; DATA-BLOCKED check passed (all official bands), but lower expected due to MT noisiness.",
        "cost": "Low-Medium (~30 s)",
        "status": "REGISTERED — needs external MT depth sounding for ground truth (free: USGS MT stations, but not needed for emission)",
    },
]

def describe_primary():
    return HYPOTHESES[0]

def all_hypotheses_markdown():
    out = ["| Rank | ID | Title | Layers | Signature | Why off-catalogue | Differs | Cost | Status |",
           "|---:|---|---|---|---|---|---|---|---|---|"]
    for h in HYPOTHESES:
        out.append(f"| {h['rank']} | {h['id']} | {h['title']} | {'; '.join(h['layers'])} | {h['signature']} | {h['why_off_catalogue']} | {h['differs']} | {h['cost']} | {h['status']} |")
    return "\n".join(out)
