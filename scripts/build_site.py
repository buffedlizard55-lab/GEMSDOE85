#!/usr/bin/env python3
"""Build the public Pages site from the fail-closed preflight state.

The builder never promotes a raster because it passes format checks. In the
current checkout the lane is unassigned, the transformed cache is unavailable,
and a binding registry-saturation certificate exists; therefore this builder
publishes a visible BLOCKED status and no download links.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))
from preflight import review, blocked_submission_registry  # noqa: E402

CSS = """
:root{--bg:#0b1220;--panel:#121d2e;--line:#304158;--fg:#eef4fa;--mut:#b3c2d1;--blue:#78b7ff;--red:#ff7777;--amber:#ffd479}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--blue)}a:hover{text-decoration:none}header{background:#070c14;border-bottom:1px solid var(--line);position:sticky;top:0}
.wrap{max-width:1020px;margin:auto;padding:16px 22px}header .wrap{display:flex;gap:22px;align-items:center;flex-wrap:wrap}
nav{display:flex;gap:16px;flex-wrap:wrap}nav a{color:var(--mut);text-decoration:none;font-size:.94rem}main{padding-bottom:56px}
h1{font-size:clamp(2rem,5vw,3.1rem);line-height:1.15;margin:28px 0 8px}h2{margin:34px 0 10px;border-bottom:1px solid var(--line);padding-bottom:8px}h3{margin:20px 0 6px}
p,li{color:#d5e0ea}.muted{color:var(--mut)}.hero{border:2px solid var(--red);background:#26161c;border-radius:16px;padding:24px;margin:22px 0}
.status{font-size:1.25rem;font-weight:900;color:#ffd6d6;letter-spacing:.02em}.card{border:1px solid var(--line);background:var(--panel);border-radius:12px;padding:18px;margin:14px 0}
.badge{display:inline-block;border:1px solid var(--red);color:#ffd6d6;padding:3px 10px;border-radius:99px;font-weight:800;font-size:.84rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.kpi{border:1px solid var(--line);border-radius:10px;padding:14px;background:#0e1827}.kpi b{font-size:1.05rem;display:block}.kpi small{color:var(--mut)}
code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#09111c;border:1px solid var(--line);border-radius:6px;padding:2px 6px;overflow-wrap:anywhere}pre{padding:14px;overflow:auto}
table{border-collapse:collapse;width:100%;margin:16px 0;display:block;overflow-x:auto}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}th{background:#19283a}
.warn{border-left:4px solid var(--amber);padding:10px 14px;background:#211c12;border-radius:0 8px 8px 0}footer{border-top:1px solid var(--line);color:var(--mut);font-size:.9rem;padding:20px 0;margin-top:38px}
"""

NAV = [
    ("index.html", "Status"),
    ("executive-summary.html", "How to submit"),
    ("hypotheses.html", "Research hypotheses"),
    ("why-h33.html", "H33 analysis"),
    ("data.html", "Data & sources"),
    ("review.html", "Audit"),
]


def _page(title: str, body: str, active: str, base: str = "") -> str:
    links = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{base}{href}"{current}>{html.escape(label)}</a>')
    nav = "".join(links)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Evidence-first DOE GEMS fault-discovery research. No submission TIFF is currently cleared.">
<title>{html.escape(title)} · GEMSDOE85</title><style>{CSS}</style></head><body>
<header><div class="wrap"><strong>GEMSDOE85 · DOE GEMS fault research</strong><nav aria-label="Main navigation">{nav}</nav></div></header>
<main class="wrap">{body}<footer>Evidence before emission · Maximize P(Win) · Own the Outcome<br>
Fault prediction is not proof of geothermal heat, permeability, flow, or a productive resource. Local format checks are not organizer acceptance.</footer></main>
</body></html>'''


def _blocker_list(card: dict) -> str:
    items = "".join(f"<li>{html.escape(str(item))}</li>" for item in card.get("blockers", []))
    return f"<ul>{items}</ul>"


def _index(card: dict) -> str:
    sat = card.get("correlation_overlap_vs_registry", {}).get("saturation_certificate", {})
    status = "Universal overlap blocker recorded" if sat.get("universal_overlap_blocker") else "Uniqueness not cleared"
    body = f'''
<h1>Submission status: blocked</h1>
<p class="muted">GEMSDOE85 is a research and audit repository for the DOE GEMS Prize Challenge (DrivenData #306).</p>
<section class="hero" aria-label="Submission decision">
  <div class="status">⛔ DO NOT DOWNLOAD OR SUBMIT</div>
  <p><strong>No new competition submission GeoTIFF is available or cleared.</strong> There is no safe one-click download on this site. Historical rasters are quarantined for research only and must not be treated as a candidate.</p>
  <span class="badge">BLOCKED — no current candidate</span>
</section>
<section class="grid" aria-label="Current evidence state">
  <div class="kpi"><b>Holdout</b><small>HOLDOUT-DTI: NOT RUN · evaluator {html.escape(card['holdout_dti']['evaluator_version'])} · no withheld-positive count or CI for a current candidate</small></div>
  <div class="kpi"><b>Uniqueness</b><small>{html.escape(status)} · no surface or final dots were compared this pass</small></div>
  <div class="kpi"><b>Format validation</b><small>NOT RUN · no candidate bytes exist to validate</small></div>
  <div class="kpi"><b>Research budget</b><small>{card['budget']['experiments_run']}/{card['budget']['experiment_limit']} experiments · {card['budget']['hours_used']}/{card['budget']['hours_limit']} hours</small></div>
  <div class="kpi"><b>Slot usage</b><small>{card['budget']['submission_slots_used']} slots used in this preflight · no selector action</small></div>
</section>
<h2>Why this is blocked</h2>
{_blocker_list(card)}
<div class="warn"><strong>Do not substitute a historical file.</strong> Passing CRS, shape, transform, and [0,1] checks proves file-format conformity only. It does not prove a method assignment, holdout improvement, uniqueness, or approval to spend a weekly competition slot.</div>
<h2>What we can say about the reported H33 result</h2>
<p>The brief reports 0.2778 for <code>h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros</code>, but the linked owner page says no organizer score existed and no submission-page receipt/hash crosswalk is present here. Treat that value as an <strong>unverified owner report, not ORGANIZER-CONFIRMED</strong>. The likely metric-level mechanism—sparse thinning can reduce redundant false-positive mass while preserving truth coverage—is plausible, but it does not establish the exact cause of that reported result. See <a href="why-h33.html">the evidence-bounded analysis</a>.</p>
<p>The prompt also gives conflicting leaderboard snapshots (0.3195 and 0.4413). Neither is re-verified in this session; do not call either the current leaderboard or an organizer-confirmed score from this repository.</p>
<h2>Research first; no slot spent</h2>
<p>Four falsifiable, qualitatively ranked geological proposals are recorded with their feature layers, transforms, missing-catalogue rationale, confounders, differences from prior local methods, and implementation costs. They remain <strong>proposals, not lane assignments or results</strong>. The top proposal was not run because the prerequisites and literal uniqueness gate are blocked.</p>
<p><a href="hypotheses.html">Read the ranked hypotheses</a> · <a href="executive-summary.html">How a future validated submission would be uploaded</a> · <a href="evidence/run_card.json">Current machine-readable run card</a>.</p>
'''
    return _page("Blocked submission status", body, "index.html")


def _executive_summary(card: dict) -> str:
    body = f'''
<h1>Executive summary — submission instructions</h1>
<section class="hero">
  <div class="status">⛔ DO NOT DOWNLOAD OR SUBMIT</div>
  <p><strong>This repository currently has no candidate GeoTIFF cleared for competition upload. No new competition submission GeoTIFF is available.</strong> No file link is provided because the lane, data/cache, and strict uniqueness gates are unresolved.</p>
  <p>Current decision: <span class="badge">BLOCKED / negative preflight</span></p>
</section>
<h2>What to do now</h2>
<ol>
<li>Do not upload any file from the historical quarantine. Those files are retained for audit/education only.</li>
<li>Read the <a href="review.html">current review</a> and <a href="hypotheses.html">ranked research proposals</a>. No weekly submission slot has been used in this preflight.</li>
<li>Wait until the status page explicitly names a new candidate and the fail-closed checks report a current holdout result, registry comparison, and on-disk format receipt. A format-only PASS is not release clearance.</li>
</ol>
<h2>When a future candidate is explicitly cleared</h2>
<p>These are the competition-site steps, not an approval of a current file:</p>
<ol>
<li>Sign in to DrivenData and open the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">GEMS Prize submissions page</a>.</li>
<li>Choose “New submission”. Select the single-band GeoTIFF named on this site's then-current green release card (or a ZIP containing exactly one such GeoTIFF, if the form permits it).</li>
<li>Paste the short note shown next to that same candidate. The note must be no more than 140 characters.</li>
<li>Submit only after checking that the candidate is approved by the separate selector and that the account's current weekly cap allows it. Save the submission-page receipt; only that receipt can establish an ORGANIZER-CONFIRMED score.</li>
</ol>
<h2>Automated format gate (future candidate only)</h2>
<p>The validator must reopen the written bytes and check a single float32 band, the competition CRS/shape/geotransform, no NaN inside the footprint, and values in [0,1]. A local format PASS does not override the lane/uniqueness/holdout gates and does not prove organizer acceptance.</p>
<p>The historical upload error <code>Predicted values must be in range [0, 1]</code> is recorded. The message alone does not identify which bad byte or nodata convention caused the previous rejection. This project therefore requires explicit finite/range checks; it does not claim that NaN outside bounds was necessarily the cause.</p>
<h2>Current machine result</h2>
<p>HOLDOUT-DTI: <strong>NOT RUN</strong> for a current candidate. Evaluator available in the pinned template: <code>{html.escape(card['holdout_dti']['evaluator_version'])}</code>. No candidate SHA-256, validator receipt, or submission name is available.</p>
<p>Manual review links: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official problem description</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official competition rules PDF</a>.</p>
'''
    return _page("How to submit (currently blocked)", body, "executive-summary.html")


def _hypotheses() -> str:
    rows = [
        {
            "rank": "1 — highest conditional research priority",
            "name": "Paired basin-interface flexure",
            "layers": "Depth-to-base surface (band 15), surface conductance (17), isostatic gravity anomaly (13); elevation and slope (12, 19) as nuisance controls.",
            "signature": "Directional, detrended cross-interface profiles with an ordered signed depth/curvature pair and a consistent gravity response; compare within matched relief/elevation strata.",
            "missing_fault": "A buried basement step beneath basin fill could retain a subsurface juxtaposition where no continuous scarp is exposed. Catalogue absence is not proof of concealment.",
            "different": "Tests signed two-flank geometry and relative displacement, rather than GEO-Pb's covariance-whitened boundary strength, gradient/ridge, or a post-placement catalogue collar.",
            "mimic": "Lateral sedimentary facies change or erosional basement relief.",
            "cost": "Medium; directional profile statistics, matching, and scale checks.",
            "gain": "Highest qualitative upside among these proposals; no numerical DTI projection and not tested.",
        },
        {
            "rank": "2",
            "name": "Gravity-curvature polarity reversal",
            "layers": "Isostatic gravity anomaly (13), vertical and horizontal gravity gradients (11, 18), gravity slope (5), and depth-to-base (15).",
            "signature": "At multiple physical scales, require an inflection bracketed by opposite signed curvature lobes and stable profile order, not simply a large gradient magnitude.",
            "missing_fault": "A covered intrabasin basement offset may preserve a density step when young sediment obscures topography.",
            "different": "Signed curvature polarity/order, not scalar gradient, worm strength, Euler depth, or orientation consensus.",
            "mimic": "An unfaulted lithologic density contact, regional detrending error, or inversion edge artifact.",
            "cost": "Medium; multiscale signed profiles and detrending controls.",
            "gain": "Moderate qualitative upside; no score measured.",
        },
        {
            "rank": "3",
            "name": "Depth-conditioned displaced magnetic edge",
            "layers": "Reduced-to-pole magnetic field (2), total magnetic intensity (14), magnetic vertical/horizontal gradients (9, 3), depth-to-base (15), and terrain slope (19).",
            "signature": "Estimate lateral displacement between magnetic edge responses at smoothing scales, conditioned on the supplied depth proxy and subdued relief; require coherent orientation and uncertainty bounds.",
            "missing_fault": "A covered continuation could leave a deeper magnetic boundary offset from the surviving surface lineament.",
            "different": "Measures scale-dependent edge displacement rather than another scalar Euler-depth estimate or line-orientation vote.",
            "mimic": "Intrusive contacts, remanent magnetization, interpolation seams, or variable survey flight height.",
            "cost": "Medium-high; displacement estimation and uncertainty/control modeling.",
            "gain": "Moderate-to-low qualitative upside; no score measured.",
        },
        {
            "rank": "4",
            "name": "Cross-drainage residual facet discontinuity",
            "layers": "Detrended elevation and slope (12, 19), optionally gravity (13) as an independent corroboration arm.",
            "signature": "Test repeatability of signed terrain-height/slope breaks across separate drainage profiles after matching elevation, aspect, and relief; do not use straight-valley occupancy.",
            "missing_fault": "A degraded fault may preserve repeated facet offsets after a continuous scarp has been eroded or buried.",
            "different": "Profile-to-profile residual consistency rather than scarp ridge thinning, valley collinearity, or a local slope peak.",
            "mimic": "Lacustrine terraces, resistant bedding, or fluvial incision.",
            "cost": "High; profile alignment, matching, and terrain-confounder controls.",
            "gain": "Lower qualitative upside and higher novelty risk; no score measured.",
        },
    ]
    table = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in (
            r["rank"], r["name"], r["layers"], r["signature"], r["missing_fault"],
            r["different"], r["mimic"], r["cost"], r["gain"])) + "</tr>"
        for r in rows
    )
    body = f'''
<h1>Ranked geological hypotheses — proposals only</h1>
<section class="hero"><div class="status">No lane is assigned; no candidate was run</div>
<p>The ranking is qualitative research judgment, not a DTI projection. The band names/order come from a prior owner-mirror INPUT-MEASUREMENT and were not revalidated in this pass. These proposals do not require a new external dataset for an initial test, but the raw stack and required transformed cache are unavailable in this checkout, so none can be validated here. Cross-repository novelty is not proven by this local shortlist.</p></section>
<table><thead><tr><th>Priority</th><th>Hypothesis</th><th>Layers</th><th>Physical signature</th><th>Why it could find a missing fault</th><th>Difference from inspected local methods</th><th>Named non-fault mimic</th><th>Implementation cost</th><th>Expected DTI upside (qualitative)</th></tr></thead><tbody>{table}</tbody></table>
<h2>Top proposal: paired basin-interface flexure</h2>
<p>It targets a buried structural juxtaposition rather than another topographic scarp. The central falsifier is whether matched, non-tectonic facies/basement transitions produce the same signed profile. Before any holdout comparison, each input feature would need its own leakage canary; catalogue-derived features, if any, must be recomputed from fold-visible faults only. Evaluation must use whole-component buffered splits, exact masking of visible faults, pooled DTI, and paired spatial-cluster uncertainty.</p>
<p><strong>Why it was not validated:</strong> the prompt gives no explicit method-paragraph assignment; the cached transformed feature stack is absent; and the binding registry saturation certificate says the literal overlap rule has a universal blocker. No lane was chosen, no experiment was run, and no weekly slot was touched.</p>
<p>Official manual-review links: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem description</a> (task, metric, format) · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN data-release page</a> · <a href="https://doi.org/10.5066/P93LGLVQ">USGS GeoDAWN DOI</a>. These external sites could not be fetched from this sandbox; links are supplied for independent manual review. The hypotheses need no additional external layer, but they do need the missing competition stack/cache.</p>
'''
    return _page("Ranked hypotheses", body, "hypotheses.html")


def _method(card: dict) -> str:
    body = f'''
<h1>Method and evidence boundary</h1>
<section class="hero"><div class="status">No current candidate method is approved</div>
<p>This page separates a plausible metric explanation of the historical H33 design from evidence about why a specific competition score occurred. The required receipt and private evaluation labels are not present.</p></section>
<h2>Why thinning can help under a distance-weighted Tversky metric</h2>
<p>The official problem-description link and prior source register specify a distance-weighted Tversky index with false-positive weight α = 0.2, false-negative weight β = 0.8, and a 300 m triangular kernel; that external page was not freshly fetched in this review. Redundant neighboring predictions may add false-positive mass without increasing the maximum truth coverage. Sparse emission can therefore improve the ratio if it removes low-credit mass while preserving coverage. That is a mechanism, not a causal finding for H33.</p>
<h2>What the local bytes establish</h2>
<p>The repository's prior H33 audit and owner page are preserved as historical evidence. The linked owner page says no organizer score existed for its artifacts; no authenticated submission receipt is present here. Consequently, the prompt's stated 0.2778 is not treated as ORGANIZER-CONFIRMED. A specific score increment cannot be explained from raster geometry alone.</p>
<ul><li>Potentially helpful mechanism: thinning reduces redundant false-positive cost under a maximum-cover metric.</li><li>Alternative explanations remain: artifact/receipt mismatch, private labels, changed scorer state, or other differences in the underlying surface.</li><li>No claim here projects a leaderboard result or proves a geothermal vent or productive reservoir.</li></ul>
<h2>Current run</h2>
<p>HOLDOUT-DTI (<code>{html.escape(card['holdout_dti']['evaluator_version'])}</code>): <strong>NOT RUN</strong> for a current candidate; no 95% CI or withheld-positive count exists. No feature-only leakage canary, registry correlation, final-dot overlap, or GeoTIFF validator was run in this preflight.</p>
<p>See the <a href="why-h33.html">full H33 evidence review</a>, <a href="review.html">repository review</a>, and <a href="hypotheses.html">four research proposals</a>.</p>
'''
    return _page("Method and evidence", body, "")


def _review(card: dict) -> str:
    gates = card.get("gates", {})
    sat = card.get("correlation_overlap_vs_registry", {}).get("saturation_certificate", {})
    core = gates.get("core_integrity", [])
    input_rows = "".join(
        f"<tr><td>{html.escape(str(row.get('id')))}</td><td>{html.escape(str(row.get('path')))}</td>"
        f"<td>{'present + hash-pinned' if row.get('ok') else 'missing / not hash-verified'}</td></tr>"
        for row in core
    ) or "<tr><td colspan=3>No valid core-input rows in the manifest.</td></tr>"
    sat_value = sat.get("covered_allowed_fraction")
    if sat_value is None:
        sat_text = "not recorded"
    else:
        sat_text = (f"{100 * float(sat_value):.1f}% ({sat.get('uncovered_allowed_pixels')} uncovered of "
                    f"{sat.get('allowed_pixels')} allowed cells)")
    sat_status = html.escape(str(sat.get("status", "certificate unavailable")))
    if sat.get("witness_path_mismatch"):
        witness_notice = (
            " Recorded witness path " + html.escape(str(sat.get("witness_file"))) +
            " differs from learning-manifest restore path " + html.escape(str(sat.get("manifest_restore_path"))) +
            "; the witness was not locally revalidated."
        )
    else:
        witness_notice = ""
    holdout = card.get("holdout_dti", {})
    body = f'''
<h1>Repository review and decision record — 2026-10-23</h1>
<section class="hero"><div class="status">⛔ No candidate TIFF is safe to download or submit</div>
<p>This is a blocked <strong>preflight</strong>, not a geological negative. No new candidate, feature canary, holdout experiment, registry comparison, format validation, or submission-slot action was performed.</p></section>
<h2>Decision gates</h2>
<table><thead><tr><th>Gate</th><th>Evidence and disposition</th></tr></thead><tbody>
<tr><td>Lane</td><td><code>registry/lane.json</code> is <strong>unassigned</strong>; the referenced method paragraph was not supplied. No lane is inferred from prior research.</td></tr>
<tr><td>Core inputs</td><td>Owner-mirror manifest results are shown below. Raw mirror consistency, where established historically, is not organizer authentication.</td></tr>
<tr><td>Transformed cache</td><td><strong>Unavailable.</strong> The pinned cache manifest is empty; raw <code>training_features.tif</code> is not present in this checkout and is not an acceptable substitute. No private cache was rebuilt.</td></tr>
<tr><td>Literal uniqueness</td><td><strong>{html.escape(sat_text)}.</strong> The binding certificate labels this REGISTRY-MEASUREMENT; witness status: {sat_status}.{witness_notice} Under the recorded positive-support rule and the allowed domain, the certificate says the literal &gt;70% stop blocks every nonempty candidate. Correlation/overlap were not measured for a new candidate.</td></tr>
<tr><td>Holdout</td><td><strong>HOLDOUT-DTI: NOT RUN.</strong> Evaluator identity: <code>{html.escape(str(holdout.get('evaluator_version')))}</code>; withheld positive count and 95% CI: unavailable for a current candidate.</td></tr>
<tr><td>Format</td><td><strong>NOT RUN.</strong> No candidate bytes exist; no SHA-256, validation receipt, or submission name is assigned.</td></tr>
<tr><td>Weekly selector</td><td>No slot selected or used. Account-specific cap/remaining quota was not accessed; a separate selector must handle it after all research gates pass.</td></tr>
</tbody></table>
<h2>Core input inventory in this checkout</h2>
<table><thead><tr><th>Manifest identity</th><th>Path</th><th>Current preflight</th></tr></thead><tbody>{input_rows}</tbody></table>
<p>The local inventory contains <code>labels.tif</code>, <code>existing_faults.tif</code>, and <code>sample_submission.tif</code>; the large transformed feature cache and raw feature raster are absent. The sample raster is a grid reference only, never a prediction.</p>
<h2>Reported H33 result: mechanism is plausible, cause is unproven</h2>
<p>The requested 0.2778 remains <strong>OWNER-REPORTED / NOT RECEIPT-VERIFIED</strong>. A historical owner page says no organizer score existed for its artifacts, and no authenticated submission-page receipt/hash crosswalk is present. Under the metric, thinning redundant predictions could reduce false-positive mass without losing a truth pixel's maximum coverage. This is a plausible mechanism only; the exact score, causal contribution, hidden-fault recall, and leaderboard comparison are not established by raster statistics. See <a href="why-h33.html">H33 analysis</a>.</p>
<h2>Ranked research proposals</h2>
<p>Four distinct geology-informed proposals are documented with named feature bands, physical transforms, a missing-catalogue rationale, local-method distinction, a named non-fault mimic, and qualitative benefit/cost. The highest-ranked is paired basin-interface flexure; its named mimic is lateral sedimentary facies change or erosional basement relief. This proposal was <strong>not assigned as a lane, not implemented, and not run</strong>. The list is not a claim of cross-repository novelty or expected numerical DTI. See <a href="hypotheses.html">ranked hypotheses</a>.</p>
<h2>Public artifacts and release safety</h2>
<p>Historical TIF/ZIP files previously present in <code>docs/downloads/</code> are removed from the Pages tree. Byte-identical artifacts already in quarantine are retained there; previously unquarantined files are moved into <code>submissions/quarantine/</code>. Nothing in that directory is cleared for submission. No direct TIFF/ZIP download link is published.</p>
<h2>Official reference links and limits</h2>
<ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData official problem description</a> (task, metric and format).</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official competition rules PDF</a> (verify current terms and cap before any slot).</li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release</a> and <a href="https://doi.org/10.5066/P93LGLVQ">DOI</a>.</li>
<li><a href="https://gdr.openei.org/submissions/1391">DOE Geothermal Data Repository / INGENIOUS listing</a>.</li>
</ul>
<p>External pages were <strong>not freshly fetched in this session</strong>; URLs are retained for manual review. Prior repository source notes are not an authenticated organizer receipt and do not prove current external availability. No new external data is required for the four initial hypotheses.</p>
<h2>Next valid step</h2>
<p>Obtain an explicit method-lane paragraph, the exact pinned transformed cache, and a policy-level resolution of the binding literal saturation blocker without weakening its 0.90 correlation or 70%/3-pixel overlap thresholds. Then perform feature-only leakage canaries, whole-component buffered holdout with fold-visible catalogue features and pixel-exact visible-fault masking, pooled DTI with paired spatial uncertainty, both registry-comparison phases, and byte-level writer validation—in that order. Stop at three experiments or two hours. No weekly slot is used by this research step.</p>
<p>Audit records: <a href="evidence/run_card.json">current machine-readable run card</a> · <a href="evidence/review_passes.json">three review passes</a> · <a href="registry/sources.json">source register</a> · <a href="registry/irregularities.json">irregularity log</a> · <a href="../research/review.md">full review notes</a>.</p>
'''
    return _page("Repository review", body, "review.html")


def _data(card: dict) -> str:
    core = card["gates"].get("core_integrity", [])
    rows = "".join(
        f"<tr><td>{html.escape(str(r['id']))}</td><td>{html.escape(str(r['path']))}</td>"
        f"<td>{'present + pinned' if r['ok'] else 'MISSING / NOT HASH-VERIFIED'}</td></tr>"
        for r in core
    ) or "<tr><td colspan=3>Manifest did not provide the four required identities.</td></tr>"
    body = f'''
<h1>Data and sources</h1>
<section class="hero"><div class="status">Inputs/cache are not ready for a new experiment</div>
<p>The local manifest describes owner-supplied GitHub mirrors. SHA-256 consistency is not organizer authentication. The competition data tab requires an authenticated DrivenData session; no account session is available here.</p></section>
<h2>Core input integrity in this checkout</h2>
<table><thead><tr><th>Identity</th><th>Expected local path</th><th>Preflight result</th></tr></thead><tbody>{rows}</tbody></table>
<p>Transformed feature-stack status: <strong>{'available' if card['gates']['cached_feature_stack_available'] else 'unavailable (no pinned cache bytes)'}</strong>. Raw features are not a substitute for the requested cache; this project does not rebuild that cache privately.</p>
<h2>Official source links for manual review</h2>
<ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS competition home</a> and <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official problem description</a>.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Competition data page</a> (login required in the access check recorded in the source registry).</li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official competition rules PDF</a>.</li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer-linked reference solution</a>.</li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN release</a> · <a href="https://doi.org/10.5066/P93LGLVQ">DOI</a>.</li>
<li><a href="https://gdr.openei.org/submissions/1391">DOE Geothermal Data Repository / INGENIOUS dataset listing</a>.</li>
</ul>
<p>External domains outside the sandbox allowlist were not freshly fetched in this session. Links are retained for manual review; see <code>registry/sources.json</code> for the recorded source class, access status, and evidence limits.</p>
'''
    return _page("Data and sources", body, "data.html")


def _research() -> str:
    body = '''
<h1>Geothermal discovery research boundary</h1>
<section class="hero"><div class="status">The competition target is faults, not geothermal production</div>
<p>A predicted fault is not proof of a geothermal vent, heat source, permeability, fluid flow, reservoir temperature, or economic resource. Any use of faults as a geothermal prior is a scientific hypothesis requiring independent thermal, geochemical, hydrologic, or geodetic evidence.</p></section>
<p>The repository's living research notes are in <a href="knowledge/geothermal-vent-discovery.md">the geothermal-vent knowledge note</a>. They distinguish historical measurements from owner-supplied mirrors, published claims whose original sources were not fetched in this review, and inference. Treat each claim according to its stated evidence class.</p>
<p>For the next analysis, see the <a href="hypotheses.html">ranked fault hypotheses</a> and <a href="data.html">source/data availability</a>. No new external dataset is proposed as viable in this session.</p>
'''
    return _page("Geothermal research", body, "")


def _sources() -> str:
    rows = [
        ("Competition task, metric, and format", "Official organizer", "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/", "Link retained; not fetched in this review."),
        ("Challenge rules", "Official rules", "https://docs.nlr.gov/docs/fy26osti/96647.pdf", "Link retained; not fetched in this review. Verify current cap/terms before any slot."),
        ("Competition data access", "Official organizer", "https://www.drivendata.org/competitions/306/competition-doe-gems/data/", "Prior source register reports login redirect; no authenticated session here."),
        ("Submission page / weekly cap", "Official organizer", "https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/", "No account-specific quota or submission receipt was accessed."),
        ("USGS GeoDAWN release", "Official USGS data release", "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and", "Link retained; not fetched in this review."),
        ("GeoDAWN DOI", "Official dataset DOI", "https://doi.org/10.5066/P93LGLVQ", "Link retained; current availability/license not rechecked."),
        ("INGENIOUS / geothermal data listing", "DOE Geothermal Data Repository", "https://gdr.openei.org/submissions/1391", "Link retained; no new external dataset downloaded or required for the ranked initial tests."),
        ("Organizer-linked reference code", "Official challenge reference", "https://github.com/drivendataorg/gems-prize-reference-solution", "Link retained; no training or execution performed in this review."),
        ("H33 owner research page", "Owner material; not an official score receipt", "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html", "Historical page says no organizer score existed for its artifacts; no authenticated receipt/hash crosswalk is present here."),
    ]
    table = "".join(
        f"<tr><td>{html.escape(kind)}</td><td><a href=\"{html.escape(url, quote=True)}\">{html.escape(url)}</a></td><td>{html.escape(status)}</td></tr>"
        for _, kind, url, status in rows
    )
    names = "".join(f"<li>{html.escape(label)}</li>" for label, _, _, _ in rows)
    body = f'''
<h1>Official-source links and evidence limits</h1>
<section class="hero"><div class="status">Links preserved; external pages not freshly fetched</div>
<p>No external webpage was fetched during this review. The table is a set of official or owner-source links for manual verification, not a claim that each page is currently available or that a score or data receipt was verified.</p></section>
<table><thead><tr><th>Source class</th><th>Link</th><th>Current access/evidence limit</th></tr></thead><tbody>{table}</tbody></table>
<h2>How to interpret the evidence</h2>
<ul>
<li>Owner-mirror SHA-256 matches establish consistency with the repository manifest, not organizer authentication.</li>
<li>A public leaderboard snapshot is not an authenticated submission-page receipt for this team. The requested H33 value is OWNER-REPORTED / NOT RECEIPT-VERIFIED.</li>
<li>Only a submission-page receipt can support an ORGANIZER-CONFIRMED score label under this project's rule.</li>
<li>The public research site is blocked: it offers no current GeoTIFF and no historical TIFF/ZIP download.</li>
</ul>
<p>Machine records: <a href="registry/sources.json">prior source-retrieval notes</a> (historical, not refreshed), <a href="registry/data_manifest.json">owner-mirror manifest</a>, and <a href="evidence/run_card.json">current blocked run card</a>.</p>
'''
    return _page("Sources and evidence limits", body, "")


def _legacy_block(title: str, landing: str) -> str:
    base = "../" if title.lower().startswith("historical duplex") else ""
    body = f'''
<h1>{html.escape(title)}</h1>
<section class="hero"><div class="status">⛔ HISTORICAL RESEARCH ONLY — DO NOT DOWNLOAD OR SUBMIT</div>
<p>This legacy lane page has no current candidate and no submission file. Its prior artifacts are quarantined for audit/education, not cleared for a competition slot.</p>
<p>Use the current <a href="{base}index.html">repository status</a>, <a href="{base}executive-summary.html">submission instructions</a>, and <a href="{base}review.html">audit record</a>.</p>
</section>
'''
    return _page(title, body, landing, base=base)


def _root_index() -> str:
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE85 — BLOCKED</title></head><body>
<h1>BLOCKED — DO NOT DOWNLOAD OR SUBMIT</h1><p>No current candidate GeoTIFF is cleared. <a href="docs/index.html">Open the research status page</a>.</p>
</body></html>'''


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(root: Path = ROOT) -> int:
    root = Path(root)
    card = review(root)
    submission = blocked_submission_registry(card)

    # Keep the canonical machine record in sync with the site generated from it.
    _write(root, "evidence/run_card.json", json.dumps(card, indent=2, allow_nan=False) + "\n")
    _write(root, "registry/submission.json", json.dumps(submission, indent=2, allow_nan=False) + "\n")

    pages = {
        "docs/index.html": _index(card),
        "docs/executive-summary.html": _executive_summary(card),
        "docs/hypotheses.html": _hypotheses(),
        "docs/method.html": _method(card),
        "docs/data.html": _data(card),
        "docs/review.html": _review(card),
        "docs/research.html": _research(),
        "docs/sources.html": _sources(),
        "docs/duplex-lane/index.html": _legacy_block("Historical duplex lane", ""),
        "docs/duplex-lane/executive-summary.html": _legacy_block("Historical duplex lane — submission instructions", ""),
        "docs/lane-h85.html": _legacy_block("Historical Lane H85", ""),
        "docs/lane-h85-executive-summary.html": _legacy_block("Historical Lane H85 — submission instructions", ""),
        "index.html": _root_index(),
    }
    for relative, content in pages.items():
        _write(root, relative, content)

    # Publish the source-led knowledge note only with its historical-evidence warning intact.
    knowledge_source = root / "knowledge/geothermal-vent-discovery.md"
    if knowledge_source.is_file():
        knowledge_target = root / "docs/knowledge/geothermal-vent-discovery.md"
        knowledge_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(knowledge_source, knowledge_target)

    # Published evidence/registry snapshots must describe the current blocked state.
    for relative in (
        "docs/evidence/run_card.json",
        "docs/evidence/saturation_certificate.json",
        "docs/evidence/review_passes.json",
        "docs/evidence/input_audit.json",
        "docs/evidence/data_restore.json",
        "docs/evidence/h33_learning_audit.json",
        "docs/registry/lane.json",
        "docs/registry/cache_manifest.json",
        "docs/registry/template_pin.json",
        "docs/registry/data_manifest.json",
        "docs/registry/sources.json",
        "docs/registry/learning_manifest.json",
        "docs/registry/submission.json",
        "docs/registry/irregularities.json",
    ):
        source = root / relative.replace("docs/", "", 1)
        if source.is_file():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return 0


def main() -> int:
    return build(ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
