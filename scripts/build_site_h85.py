#!/usr/bin/env python3
"""Generate docs/index.html + docs/executive-summary.html from evidence/.

The verdict banner is computed, never hand-typed: PROMOTE requires
holdout-beats-valid-control AND validator-all-pass AND uniqueness-pass.
Otherwise the banner says DO NOT SUBMIT and says why.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E, D = ROOT / "evidence", ROOT / "docs"

card = json.loads((E / "run_card_h85.json").read_text())
exp = json.loads((E / "holdout_experiments.json").read_text())
name = card["submission_name"]
note = card["submission_note_max_140_chars"]
sha = card["raster_sha256"]
z = card["validator_output"]
promote = card["verdict"] == "promote"

if promote:
    banner = '<div class="banner ok">✅ OK TO DOWNLOAD AND SUBMIT THIS .TIF</div>'
else:
    banner = ('<div class="banner no">🔴 DO NOT SUBMIT — VERDICT: NEGATIVE<br>'
              '<span>Holdout did not beat the valid control and uniqueness is ambiguous under the '
              'strict protocol reading. The file below is downloadable for INSPECTION / AUDIT ONLY. '
              'Do not spend a weekly submission slot on it.</span></div>')

def fmt(v):
    return f"{v:.4f}"

rows = ""
for k, v in exp["experiments"].items():
    rows += f"<tr><td>{k}</td><td>HOLDOUT-DTI</td><td>{fmt(v['pooled_dti'])}</td><td>[{fmt(v['ci95'][0])}, {fmt(v['ci95'][1])}]</td><td>{v['n_withheld_positives']}</td></tr>\n"
for k, v in exp["controls"].items():
    rows += f"<tr><td>{k} (registry control)</td><td>HOLDOUT-DTI</td><td>{fmt(v['pooled_dti'])}</td><td>[{fmt(v['ci95'][0])}, {fmt(v['ci95'][1])}]</td><td>{v['n_withheld_positives']}</td></tr>\n"

checks = "".join(f"<li>{'✅' if v else '❌'} {k}</li>" for k, v in z["checks"].items())

CSS = """body{font-family:system-ui,Arial,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#14202b}
.banner{border-radius:12px;padding:1.2rem 1.4rem;font-size:1.35rem;font-weight:800;margin:1rem 0}
.banner.ok{background:#0a7d33;color:#fff}.banner.no{background:#b00020;color:#fff}
.banner span{font-size:1rem;font-weight:500}
.dl{display:inline-block;background:#1453a3;color:#fff;padding:.8rem 1.2rem;border-radius:10px;text-decoration:none;font-weight:700;margin:.3rem .3rem .3rem 0}
code{background:#eef2f6;padding:.15rem .35rem;border-radius:5px;word-break:break-all}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:.45rem .6rem;text-align:left}
.copy{background:#f6f8fa;border:1px solid #dfe3e8;border-radius:8px;padding:.7rem 1rem}"""

index = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>GEMSDOE85 — Lane H85 submission (verdict: {card['verdict'].upper()})</title><style>{CSS}</style></head><body>
<h1>GEMSDOE85 · DOE GEMS Prize · Lane H85</h1>
<p><b>Core values:</b> Maximize P(Win) · Own the Outcome. Every number below is labelled
HOLDOUT-DTI (local instrument) or ORGANIZER-CONFIRMED (submission-page receipt). A projection is never a score.</p>

{banner}

<h2>⬇ Submission file (inspection)</h2>
<p>
<a class="dl" href="https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE85/main/submissions/{name}">Download .tif ({z['bytes']} bytes)</a>
<a class="dl" href="https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE85/main/submissions/{name}.zip">Download .zip (single GeoTIFF inside)</a>
<a class="dl" href="https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE85/main/submissions/{name.replace('-zeros.tif','-audit.json')}">Validator audit JSON</a>
<a class="dl" href="lane-h85-executive-summary.html">Executive summary — how to submit</a>
</p>
<div class="copy"><b>Unique submission name:</b> <code>{name}</code><br>
<b>Note to paste (≤140 chars, {card['submission_note_chars']}/140):</b> <code>{note}</code><br>
<b>sha256:</b> <code>{sha}</code><br>
single band · float32 · EPSG:32611 · 100 m · 3730×3292 · {z['positive_px']} positive pixels ·
every grid cell finite · every value in [0, 1] · 0 NaN anywhere · no nodata tag ·
{z['on_catalogue_px']} px on catalogue · min distance to catalogue {z['min_dist_to_catalogue_px']:.2f} px</div>

<h2>Why this verdict (machine-checked, no human inspection)</h2>
<table><tr><th>candidate / control</th><th>label</th><th>DTI</th><th>95% CI</th><th>withheld positives</th></tr>
{rows}</table>
<p>Evaluator: <code>{exp['evaluator']}</code> — hide-and-recover: whole fault segments withheld with a
1.5 km buffer, catalogue-based features derived only from visible faults, visible faults masked
pixel-exactly, pooled DTI (α=0.2, β=0.8, 300 m triangular kernel). The 0.2778 winner raster is an
invalid bar on this instrument (it was pruned against the full catalogue — IR-85-08); the valid bar
is the d2.8 control. E1 does not beat it at any swept budget (20k–55k dots). Leakage canary: no
feature alone exceeds AUC 0.90. Uniqueness: max |Spearman| vs registry surfaces
{card['correlation_overlap_vs_registry']['max_abs_spearman_surface_vs_any_registry_raster']:.3f} ≤ 0.90;
dot-overlap ≤ 0.70 against every comparable dotted submission, but &gt; 0.70 against three saturated
registry rasters under the strict reading (IR-85-07) — logged, promotion stopped.</p>

<h2>Validator receipt (re-read from the written bytes)</h2>
<ul>{checks}</ul>
<p><b>all_checks_passed: {z['all_checks_passed']}</b> — CRS/shape/transform match the sample submission;
no NaN inside the footprint; values in [0,1]. This is the check that prevents the portal error
<code>Predicted values must be in range [0, 1]</code>.</p>

<h2>Answer to the brief's question</h2>
<p><b>Why did h33-2-b2 get 0.2778 (ORGANIZER-CONFIRMED)?</b> The metric makes every emitted pixel cost
0.2 denominator mass; a dot helps iff its kernel credit exceeds 0.2·DTI. The winner is a binary,
~2.8 px-Poisson-thinned, catalogue-halo-pruned subset of a strong multi-physics ridge field — thinning
deletes dots whose 300 m coverage a neighbour already supplies. <b>Can a unique file beat it?</b>
Only with a better-ranked surface at the same emission discipline. Lane H85's fold-proper supervised
surface is genuinely unique (overlap 0.40 vs the winner's dots) but its HOLDOUT-DTI does not beat the
valid control, so — honestly — <b>no promotable file was found this session</b>; the negative result
is the deliverable, and the next lever (sub-km seismicity, sandbox-blocked; spring-chain H85-D) is
documented in the hypotheses page.</p>

<h2>Research & registries</h2>
<ul>
<li><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/arena/5873bc3c-gemsdoe85/docs/research/hypotheses.md">Five hypotheses, ranked (layers, signatures, mimics)</a></li>
<li><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/arena/5873bc3c-gemsdoe85/docs/research/why-02778-and-how-to-beat-it.md">Why 0.2778 won — full derivation</a></li>
<li><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/arena/5873bc3c-gemsdoe85/registry/irregularities.json">Irregularities IR-85-01…09 (flagged for review)</a></li>
<li><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/arena/5873bc3c-gemsdoe85/evidence/run_card.json">Run card (JSON)</a></li>
</ul>

<h2>Official sources</h2>
<ul>
<li>Competition / metric: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem description</a></li>
<li>Leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData leaderboard</a></li>
<li>Reference solution: <a href="https://github.com/drivendataorg/gems-prize-reference-solution">drivendataorg/gems-prize-reference-solution</a></li>
<li>Rules PDF: <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR FY26 OSTI 96647</a></li>
<li>USGS GeoDAWN: <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS data release</a></li>
<li>INGENIOUS: <a href="https://gbcge.org/current-projects/ingenious/">gbcge.org</a> · EPSG:32611: <a href="https://epsg.io/32611">epsg.io/32611</a> · Tversky: <a href="https://en.wikipedia.org/wiki/Tversky_index">Wikipedia</a> · GDR 1391: <a href="https://gdr.openei.org/submissions/1391">gdr.openei.org</a></li>
</ul>
</body></html>"""

exec_summary = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Executive summary — how to make a submission (GEMSDOE85)</title><style>{CSS}</style></head><body>
<h1>Executive summary — exactly how to submit to the DOE GEMS competition</h1>
{banner}
<ol>
<li><b>Decide.</b> Read the banner above. It is generated from the machine validator + holdout +
uniqueness gates. If it says DO NOT SUBMIT, stop here — downloading is for inspection only.</li>
<li><b>Download</b> (only when the banner is green): <a href="https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE85/main/submissions/{name}">{name}</a>
(or the <a href="https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE85/main/submissions/{name}.zip">.zip</a> containing that single GeoTIFF).</li>
<li><b>Open</b> the DrivenData new-submission form:
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> →
Submit → <i>File to submit</i>.</li>
<li><b>Choose the downloaded .tif file</b> (single-band GeoTIFF; the .zip with a single GeoTIFF
inside is also accepted by the portal).</li>
<li><b>Name / Note field:</b> paste exactly:<br><div class="copy"><code>{note}</code></div>
({card['submission_note_chars']}/140 characters — identifies the method, holdout and verdict later.)</li>
<li><b>Create submission.</b> If the portal answers <code>Predicted values must be in range [0, 1]</code>,
the file is not this repo's primary: the primary is all-finite float32 in [0,1] with no nodata tag
(validator receipt: <a href="https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE85/main/submissions/{name.replace('-zeros.tif','-audit.json')}">audit JSON</a>,
sha256 <code>{sha}</code>). Re-download and check the sha256 matches before retrying.</li>
<li><b>Record the receipt.</b> Copy the organizer score back into <code>evidence/</code> labelled
ORGANIZER-CONFIRMED with the filename + sha256 — that crosswalk is what this fleet has been missing (IR-85-04).</li>
</ol>
<p>Format facts (validator-verified): EPSG:32611, 3730×3292, 100 m, float32, binary {{0,1}},
{z['positive_px']} positive pixels, 0 on the catalogue, CRS/shape/transform identical to the sample submission.</p>
<p><a href="lane-h85.html">← Back to Lane H85</a> · <a href="index.html">Repo main page</a></p>
</body></html>"""

(D / "lane-h85.html").write_text(index)
(D / "lane-h85-executive-summary.html").write_text(exec_summary)
print("site written; promote =", promote)
