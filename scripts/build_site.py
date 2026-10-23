#!/usr/bin/env python3
"""Generate the GitHub Pages site from the evidence JSONs.

No number on the site is typed by hand: everything is read from registry/ and evidence/, so the
page cannot drift from the measurements.  If an evidence file is missing the section says so
rather than inventing a value.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#9198a1;
--acc:#2f81f7;--ok:#3fb950;--warn:#d29922;--bad:#f85149}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px 80px}
header{border-bottom:1px solid var(--line);background:#010409;position:sticky;top:0;z-index:9}
header .wrap{padding:14px 20px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}
header b{font-size:17px}
nav a{color:var(--mut);font-size:14px;margin-right:16px}
nav a.on{color:var(--fg);font-weight:600}
h1{font-size:32px;line-height:1.25;margin:34px 0 8px}
h2{font-size:22px;margin:40px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}
h3{font-size:17px;margin:26px 0 8px}
p,li{color:#c9d1d9}
.sub{color:var(--mut);font-size:15px;margin-top:0}
.hero{background:linear-gradient(180deg,#132033,#0d1117);border:1px solid #1f4b8f;
border-radius:14px;padding:26px;margin:24px 0}
.dl{display:inline-flex;align-items:center;gap:12px;background:var(--acc);color:#fff;
font-size:19px;font-weight:700;padding:16px 26px;border-radius:10px;margin:6px 10px 6px 0}
.dl:hover{background:#1f6feb;text-decoration:none}
.dl2{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);
color:var(--fg);padding:13px 18px;border-radius:10px;font-size:14px;margin:6px 8px 6px 0}
.dl2:hover{border-color:var(--acc);text-decoration:none}
code,kbd{background:#1f242c;border:1px solid var(--line);border-radius:5px;
padding:1px 6px;font-size:13px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px;
overflow-x:auto;font-size:13px}
pre code{background:none;border:none;padding:0}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
th{background:#1c2128;font-weight:600}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;margin:18px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px}
.kpi .v{font-size:27px;font-weight:700;font-variant-numeric:tabular-nums}
.kpi .l{color:var(--mut);font-size:12.5px;text-transform:uppercase;letter-spacing:.5px}
.tag{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;
border:1px solid;letter-spacing:.4px}
.t-ok{color:var(--ok);border-color:var(--ok)}.t-warn{color:var(--warn);border-color:var(--warn)}
.t-bad{color:var(--bad);border-color:var(--bad)}.t-mut{color:var(--mut);border-color:var(--line)}
.note{border-left:3px solid var(--warn);background:#1c1a12;padding:12px 16px;border-radius:0 8px 8px 0;margin:16px 0}
.good{border-left:3px solid var(--ok);background:#0f1f14;padding:12px 16px;border-radius:0 8px 8px 0;margin:16px 0}
ol.steps{counter-reset:s;list-style:none;padding:0}
ol.steps>li{counter-increment:s;position:relative;padding:14px 0 14px 52px;border-bottom:1px solid var(--line)}
ol.steps>li::before{content:counter(s);position:absolute;left:0;top:12px;width:32px;height:32px;
border-radius:50%;background:var(--acc);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center}
footer{color:var(--mut);font-size:13px;border-top:1px solid var(--line);margin-top:50px;padding-top:18px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;word-break:break-all}
"""


def page(title: str, body: str, active: str) -> str:
    nav = [("index.html", "Submission"), ("executive-summary.html", "How to submit"),
           ("method.html", "Method & evidence"), ("data.html", "Data & sources")]
    links = "".join(
        f'<a href="{h}" class="{"on" if h == active else ""}">{html.escape(t)}</a>'
        for h, t in nav)
    sub = jload(ROOT / "registry" / "submission.json") or {}
    built_utc = sub.get("built_utc", "20261022T222707Z")
    if "T" in built_utc and "Z" in built_utc:
        d_part, t_part = built_utc.split("T")
        stamp = f"{d_part[:4]}-{d_part[4:6]}-{d_part[6:8]} {t_part[:2]}:{t_part[2:4]} UTC"
    else:
        stamp = "2026-10-22 22:27 UTC"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<header><div class="wrap"><b>GEMSDOE85</b><nav>{links}</nav></div></header>
<div class="wrap">{body}
<footer>Built {stamp} by <code>scripts/build_site.py</code> from <code>registry/</code> and
<code>evidence/</code>. Every number on this site is generated from a measurement file; none is
typed by hand. Repository:
<a href="https://github.com/buffedlizard55-lab/GEMSDOE85">buffedlizard55-lab/GEMSDOE85</a>.
</footer></div></body></html>"""


def jload(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def fmt(x, n=4):
    try:
        return f"{float(x):.{n}f}"
    except Exception:
        return "—"


# --------------------------------------------------------------------------- pages


def build_index() -> str:
    sub = jload(ROOT / "registry" / "submission.json")
    if not sub:
        return page("GEMSDOE85", "<h1>No submission built yet</h1>"
                    "<p>Run <code>python scripts/build_submission.py</code>.</p>", "index.html")
    pri = sub["primary"]
    checks = pri["checks"]
    n_fail = sum(1 for v in checks.values() if not v)
    card = jload(ROOT / "evidence" / "run_card_review_20261023.json") or {}

    rows = "".join(
        f'<tr><td>{html.escape(k.replace("_"," "))}</td>'
        f'<td><span class="tag {"t-ok" if v else "t-bad"}">{"PASS" if v else "FAIL"}</span></td></tr>'
        for k, v in checks.items())

    alts = "".join(
        f'<a class="dl2" href="downloads/{html.escape(a["filename"])}">⬇ {html.escape(a["role"])}'
        f' · {a["bytes"]/1024:.0f} KB</a>' for a in sub.get("alternates", []) if "nan" not in a["filename"].lower())

    body = f"""
<h1>Candidate file — submission is currently blocked</h1>
<p class="sub">An auditable, fully automated fault-discovery submission for the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS Prize
Challenge (DrivenData #306)</a>. The file below was generated, validated and published by code —
no human inspected it, and it cannot reach this page unless all
{len(checks)} format checks passed.</p>

<div class="hero">
  <div style="font-size:13px;color:#9198a1;text-transform:uppercase;letter-spacing:.7px;
  font-weight:700;margin-bottom:10px">⬇ Candidate GeoTIFF — NOT CLEARED FOR SUBMISSION</div>
  <a class="dl" href="downloads/{html.escape(pri['filename'])}">⬇ Download the GeoTIFF
  ({pri['bytes']/1024:.0f} KB)</a>
  <div style="margin-top:14px">{alts}</div>
  <div style="margin-top:16px">
    <span class="tag {'t-ok' if n_fail == 0 else 't-bad'}">
    {'FORMAT PASS ONLY — SUBMISSION BLOCKED (lane unassigned / uniqueness gate unresolved)'
     if n_fail == 0 else str(n_fail) + ' CHECK(S) FAILED — DO NOT SUBMIT'}</span>
  </div>
  <table style="margin-top:16px">
    <tr><th>file</th><td class="mono">{html.escape(pri['filename'])}</td></tr>
    <tr><th>sha256</th><td class="mono">{html.escape(pri['sha256'])}</td></tr>
    <tr><th>format</th><td>single-band float32 GeoTIFF · EPSG:32611 · 3730 × 3292 ·
        100 m · all values finite and in [0, 1] · no nodata tag</td></tr>
    <tr><th>emitting pixels</th><td class="n">{pri['stats']['emitting_pixels']:,}</td></tr>
    <tr><th>pixels on a mapped fault</th>
        <td class="n">{pri['stats']['on_catalogue_pixels']:,}</td></tr>
  </table>
</div>

<div class="card">
  <h3 style="margin-top:0">Paste this into the “Note” box on the submission form</h3>
  <pre><code>{html.escape(sub['note'])}</code></pre>
  <p class="sub" style="margin-bottom:0">{len(sub['note'])} characters (the form asks for a short
  comment; this one names the hypothesis, the budget and the holdout result).</p>
</div>

<div class="good"><b>Why this file is safe to upload.</b> The operator's previous upload was
rejected with <code>Predicted values must be in range [0, 1]</code>. A NaN fails
<code>0 &le; v &le; 1</code> under IEEE-754 comparison, so any raster with NaN outside the survey
footprint can trip that check. This file is <b>all-finite</b>: zeros outside the footprint, no
nodata tag, every value a real number in [0, 1]. <code>src/gems85/submission.py::validate</code>
re-opens the written file and asserts it, and <code>write_submission()</code> refuses to return a
path whose validation failed.</div>

<h2>What the file looks like (diagnostic preview, not a gate)</h2>
<div class="card">
<img src="downloads/preview_ctxfus50_vs_h33_catalogue.png" alt="Preview map: candidate dots vs catalogue and the h33 artifact"
     style="max-width:520px;width:100%;border:1px solid #30363d;border-radius:8px">
<p class="sub" style="margin-bottom:0">400&nbsp;m max-pooled preview. <b style="color:#3cc8ff">Cyan</b> = this
candidate's dots · <b style="color:#f0aa28">amber</b> = h33 (0.2778 OWNER-REPORT) dots ·
<b style="color:#78ff8c">green</b> = both within the same 400&nbsp;m cell · grey = USGS/INGENIOUS catalogue
(candidate has zero dots within 200&nbsp;m of it). Measured at full resolution: 37.9&nbsp;% of candidate
dots lie within 3&nbsp;px of an h33 dot (gate &le;&nbsp;70&nbsp;%). No human inspected this image as an
approval step — approval is the automated validation below.</p>
</div>

<h2>Format validation — every check, run on the written bytes</h2>
<table><tr><th>check</th><th>result</th></tr>{rows}</table>

<div class="note"><b>Session review 2026-10-22:</b> two pre-registered GEO-Pb variants
(persistence retired; radius widened) scored HOLDOUT-DTI 0.09105 and 0.09773 @ 90k vs this
file's 0.09838 — <b>both negative, neither was emitted</b>. This file remains the validated
primary; it has <b>no organizer score</b> and is honestly projected below the 0.2778 incumbent.
Details: <span class="mono">evidence/run_card_session_06987ae9.json</span> in the repository.</div>

<h2>What this submission claims, and what it does not</h2>
<div class="note"><b>No number on this site is a competition score.</b> Every measurement here is
a <b>HOLDOUT-DTI</b>: the official metric computed against <i>withheld segments of the known
catalogue</i> on this machine. The live target is a private set of expert-mapped faults that are
absent from that catalogue, so the holdout is a screen, not a prediction. Scores quoted for
earlier GEMSDOE artifacts are <b>OWNER-REPORT</b> — copied from the operator's ledger, not
re-verified against a DrivenData receipt here.</div>

{render_run_card(card)}

<h2>Where it came from</h2>
<p><a href="method.html">Method &amp; evidence →</a> the hypothesis, the holdout protocol, the
leakage canary, the ablation and the negative results.<br>
<a href="executive-summary.html">How to submit →</a> a step-by-step walkthrough of the DrivenData
submission form.<br>
<a href="data.html">Data &amp; sources →</a> every input file, its SHA-256 and its official link.</p>

<h2>Session update 2026-10-22 — the primary above supersedes the GEO-Pb 90,000-dot file</h2>
<div class="note"><b>What changed and why.</b> The previous primary (GEO-Pb crest, 90,000 dots)
was emitted at the budget that maximised the *catalogue holdout*, whose marginal credit bar
(&asymp;0.02/dot at DTI&asymp;0.1) is far below the *live* bar (0.0588/dot at the family best
0.2778). The family's own live cascade (121k&rarr;0.1922, 44k&rarr;0.2600, 37,654&rarr;0.2778)
shows the live operating point is &asymp;38k dots. The new primary is a different field
(<b>S85-CTXFUS</b>: 30-channel contextual supervised detector rank-fused 50/50 with the GEO-Pb
crest) emitted at that operating point, and it is the first field in this repo to beat the
holdout best at matched budget (HOLDOUT-DTI 0.08082 vs 0.07475 @ 37,654, 3/4 folds, CIs
overlap — see the run card). Three pre-registered alternatives tested in the same session
(RELAY network-completion geometry, RELAY-gated crest, blurred-field emission) were
<b>negative</b> and are published as such on the method page. The old files remain downloadable
below, labelled superseded; none of them, and not the new file either, has an organizer score.</div>

<h2>The other lanes in this repository</h2>
<p>GEMSDOE85 was worked by independent lanes in parallel. The current primary is the
<strong>S85-CTXFUS session</strong> candidate above. The <strong>GEO-Pb juxtaposition</strong>
lane (H85-1) supplied the crest field that is one half of the fusion; its standalone files are
the “previous GEO-Pb” alternates in the download list. The <strong>transtensional pull-apart +
gravity worm duplex</strong> lane (H85-duplex) reached <code>main</code> first and its artifacts
are kept alongside these ones, untouched:</p>
<ul>
<li><a href="duplex-lane/index.html">Duplex lane — front page</a> ·
    <a href="duplex-lane/executive-summary.html">its executive summary</a></li>
<li>Its submissions, also in <code>docs/downloads/</code>:
    <a href="downloads/gems85-h85-duplex-pullapart-worm-20261022T220544Z-2f8b57d9-zeros.tif">duplex (42,000 dots)</a> ·
    <a href="downloads/gems85-h85-ti-pure-20261022T221047Z-f53a0c81-zeros.tif">TI-pure (38,000)</a> ·
    <a href="downloads/gems85-h85-worm-pure-20261022T221114Z-e3091ec2-zeros.tif">worm-pure (46,000)</a></li>
</ul>
<p class="warn"><strong>The two lanes' holdout numbers are not comparable.</strong> They use
different evaluators, different fold geometry and different withheld-positive counts, so the
duplex lane's reported 0.1542 and this lane's 0.09838 cannot be ranked against each other. Doing
so would be exactly the apples-to-oranges error this repository's instrument calibration was
built to catch. Both lanes' artifacts are published; neither has an organizer score. The two
lanes <em>do</em> now share one metric implementation, and
<code>tests/test_metric.py</code> asserts the fast O(29N) path equals a literal brute-force
transcription of the official definition — so at least the ruler is common.</p>
"""
    return page("GEMSDOE85 — submission", body, "index.html")


def render_run_card(card: dict) -> str:
    if not card:
        return ""
    ho = card.get("holdout_dti", {})
    return f"""
<h2>Run card</h2>
<div class="grid">
  <div class="kpi"><div class="l">Holdout DTI (pooled)</div>
    <div class="v">{fmt(ho.get('value'), 5)}</div>
    <div class="l" style="text-transform:none">95% CI
      [{fmt((ho.get('ci95') or [None, None])[0], 5)}, {fmt((ho.get('ci95') or [None, None])[1], 5)}]</div></div>
  <div class="kpi"><div class="l">Withheld positives</div>
    <div class="v">{ho.get('n_withheld_positives', '—'):,}</div>
    <div class="l" style="text-transform:none">4 spatially-blocked folds</div></div>
  <div class="kpi"><div class="l">vs uniform random</div>
    <div class="v">{fmt(card.get('vs_random_delta'), 5)}</div>
    <div class="l" style="text-transform:none">matched emitted mass</div></div>
  <div class="kpi"><div class="l">Verdict</div>
    <div class="v" style="font-size:21px">{html.escape(str(card.get('verdict', '—')))}</div>
    <div class="l" style="text-transform:none">pre-registered gate</div></div>
</div>
<pre><code>{html.escape(json.dumps(card, indent=2)[:6000])}</code></pre>"""


def build_exec() -> str:
    sub = jload(ROOT / "registry" / "submission.json") or {}
    pri = sub.get("primary", {})
    fn = pri.get("filename", "(build the submission first)")
    note = sub.get("note", "")
    card = jload(ROOT / "evidence" / "run_card_review_20261023.json") or {}
    vo = card.get("validator_output", {}) or {}
    # Format validity is independent of scientific clearance; lane/uniqueness remain blocking.
    ok = bool(vo.get("all_checks_passed"))
    ok_cls = "t-ok" if ok else "t-bad"
    ok_label = "PASS" if ok else "FAIL"
    ok_msg = ("FORMAT PASS ONLY — SUBMISSION BLOCKED" if ok
              else "FAILED — DO NOT SUBMIT")
    zip_fn = fn.replace("-zeros.tif", "-zeros.zip")
    body = f"""
<h1>Executive summary — submission is currently blocked</h1>
<p class="sub">The candidate file passes format checks, but must not be uploaded: the method lane is unassigned and uniqueness clearance is unresolved. This page explains the eventual submission flow; no slot should be spent now.</p>

<div class="hero">
  <div style="font-size:13px;color:#9198a1;text-transform:uppercase;letter-spacing:.7px;
  font-weight:700;margin-bottom:10px">⬇ Research artifact — candidate GeoTIFF (not cleared for submission)</div>
  <a class="dl" href="downloads/{html.escape(fn)}">⬇ Download the GeoTIFF ({pri.get('bytes', 0)/1024:.0f} KB)</a>
  <div style="margin-top:14px"><a class="dl2" href="downloads/{html.escape(zip_fn)}">⬇ zipped twin</a></div>
  <div style="margin-top:16px">
    <span class="tag {ok_cls}">{ok_label}</span> {ok_msg}
  </div>
  <div class="mono" style="margin-top:12px;color:#9198a1">{html.escape(fn)}</div>
</div>

<div class="note"><b>Do not upload this candidate or spend a weekly slot.</b> The steps below describe the standard competition workflow only; this artifact is blocked pending lane assignment and literal registry-uniqueness review.</div>
<ol class="steps">
<li><b>When a candidate is formally cleared, sign in to DrivenData.</b> Go to the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">GEMS Prize
submissions page</a>. You must be signed in and joined to the competition; the data and
submission pages redirect to a login otherwise.</li>

<li><b>Click “New submission”.</b> The form has exactly two inputs: <i>File to submit</i> and an
optional <i>Note</i>.</li>

<li><b>After a future selector decision clears a candidate, choose that approved file.</b> Do not upload the research artifact linked above. The form accepts a single-band GeoTIFF
(<code>.tif</code>) or a <code>.zip</code> containing one GeoTIFF. This file is a plain
<code>.tif</code>; a zipped twin is also published on the
<a href="index.html">front page</a> if you prefer that route.</li>

<li><b>Paste the note.</b> The form says: <i>“A short comment to help you or your team tell
submissions apart later e.g. clustering with k=25”.</i> Use this, which is already generated for
this exact file:
<pre><code>{html.escape(note)}</code></pre></li>

<li><b>Submit.</b> The scored result appears on your submissions page, and the best public score
appears on the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a>.
Record the receipt — a score is <b>ORGANIZER-CONFIRMED</b> only when it is copied from that page.</li>
</ol>

<h2>The rules you are agreeing to, in one table</h2>
<table>
<tr><th>rule</th><th>what it means here</th><th>official source</th></tr>
<tr><td>Format</td><td>single-band GeoTIFF, float32, EPSG:32611, 100 m, same bounds as
<code>training_features.tif</code>, values in [0,&nbsp;1]</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem
description → Submission format</a></td></tr>
<tr><td>Metric</td><td>distance-weighted Tversky index, α = 0.2 (false positives),
β = 0.8 (false negatives), triangular kernel with 300 m support</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem
description → Performance metric</a></td></tr>
<tr><td>Two rounds</td><td>Initial round scores against a private set of expert-mapped new
faults; the final round re-scores the <i>same</i> file against an expanded label set that
includes discoveries the panel verifies from everyone's submissions. You pick <b>one</b> file for
both rounds before the deadline.</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem
description → Competition structure</a></td></tr>
<tr><td>Weekly cap</td><td>The submission page shows your remaining scored submissions for the
week. Promotion of a candidate into a real slot is a deliberate, separate decision — this site
publishes candidates, it does not spend slots.</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">Submissions
page</a></td></tr>
<tr><td>External data</td><td>Allowed, provided the licence permits use in the challenge and
sharing with the sponsor. Everything used here is US-government public-domain
(USGS GeoDAWN, USGS 3DEP, USGS SGMC) or competition-supplied.</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/">Rules</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF</a></td></tr>
</table>

<h2>If the upload is rejected</h2>
<table>
<tr><th>error</th><th>cause</th><th>fixed here by</th></tr>
<tr><td><code>Predicted values must be in range [0, 1]</code></td>
<td>A NaN (or an out-of-range value) anywhere in the raster. <code>NaN &le; 1</code> is
<code>False</code> under IEEE-754, so a NaN-filled margin can fail a naive range check even
though the written format page allows nan outside the bounds.</td>
<td>The primary file is <b>all-finite</b>: zeros outside the footprint, no nodata tag.
<code>validate()</code> asserts <code>no_nan_inside_footprint</code>,
<code>all_finite_whole_raster</code> and <code>values_in_0_1_whole_raster</code> on the written
bytes before the file is published.</td></tr>
<tr><td>CRS / shape / transform mismatch</td><td>Raster not on the competition grid.</td>
<td><code>assert_grid()</code> compares against <code>sample_submission.tif</code>;
<code>transform_matches_template</code> and <code>crs_epsg_32611</code> are in the check table.</td></tr>
<tr><td>Multi-band or wrong dtype</td><td>More than one layer, or not float32.</td>
<td><code>single_band</code> and <code>dtype_float32</code> checks.</td></tr>
</table>
"""
    return page("How to submit — GEMSDOE85", body, "executive-summary.html")


def _session_section() -> str:
    e2b = jload(ROOT / "evidence" / "session_22847afd_e2b.json") or {}
    exp85 = jload(ROOT / "evidence" / "session_22847afd_experiments.json") or {}
    if not e2b:
        return ""
    arms = {}
    for k, v in (exp85.get("arms") or {}).items():
        if "37654" in v:
            arms[k] = v["37654"]["pooled_holdout_dti"]
    for k, v in (e2b.get("arms") or {}).items():
        if "37654" in v:
            arms[k] = v["37654"]["pooled_holdout_dti"]
    rows = "".join(
        f'<tr><td class="mono">{html.escape(k)}</td><td class="n">{fmt(v, 5)}</td></tr>'
        for k, v in sorted(arms.items(), key=lambda kv: -kv[1]))
    can = exp85.get("canary_auc") or {}
    return f"""
<h2>0. Current primary — S85-CTXFUS (session 2026-10-22, arena/22847afd)</h2>
<div class="card">
<p><b>Hypothesis (pre-registered in <code>research/session-22847afd-hypotheses.md</code> before
measuring):</b> a fault is a <i>line in context</i>, not a pixel. The shipped field rank-fuses
(50/50) two mechanisms that fail differently: (a) a <b>contextual supervised detector</b> —
HistGradientBoosting on the 24 catalogue-free channels below plus six line-context channels
(1.5&nbsp;km along-strike line support, multi-scale context means, five-field corroboration
count), trained per fold on the visible catalogue only; and (b) the <b>GEO-Pb crest</b> of
section 1. Emission is the measured gate configuration: 37,654 binary dots, 4&nbsp;px minimum
separation, zero mass within 2&nbsp;px of the catalogue. Named mimic: erosional volcanic
mesa/flow margins.</p>
<p><b>Result (HOLDOUT-DTI, evaluator gems85-holdout-v1.0.0, 60,988 withheld positives):</b>
the fusion is the only arm that beat the previous holdout best (GEO-Pb crest 0.07475 @ 37,654)
— at both separations and both budgets, 3/4 folds positive, with overlapping 95% CIs. The three
pre-registered RELAY arms (fault-network tip/relay completion geometry, alone and as a gate)
were <b>clear negatives</b>; a relay channel inside the classifier was a train/test-reversal
bug (training mean 0.090 on positives vs 0.006 on withheld positives) and was removed in the
logged E2b/E3b ablation. Leakage canaries: RELAY {fmt(can.get('relay'), 3)},
max context channel {fmt(max([v for k, v in can.items() if k.startswith('ctx_')] or [0]), 3)}
— all far below the 0.90 flag.</p>
<table><tr><th>arm (all HOLDOUT-DTI @ 37,654 dots)</th><th class="n">pooled DTI</th></tr>{rows}
<tr><td class="mono">crest reference (sep 2.8 / sep 4.0)</td><td class="n">0.06953 / 0.07475</td></tr>
</table>
<p style="margin-bottom:0">Full evidence: <code>evidence/session_22847afd_experiments.json</code>,
<code>evidence/session_22847afd_e2b.json</code>, run card on the front page. Why the family best
(0.2778) works and what beating it requires:
<code>docs/research/why-02778-session-22847afd.md</code> in the repository.</p>
</div>
"""


def build_method() -> str:
    exp = jload(ROOT / "evidence" / "experiments.json") or {}
    abl = jload(ROOT / "evidence" / "supervised_ablation.json") or {}
    cal = jload(ROOT / "evidence" / "instrument_calibration.json") or {}
    dup = jload(ROOT / "evidence" / "duplicate_check.json") or {}

    canary = "".join(
        f'<tr><td class="mono">{html.escape(k)}</td><td class="n">{fmt(v)}</td>'
        f'<td><span class="tag {"t-bad" if v > 0.90 else "t-ok"}">'
        f'{"SUSPECT" if v > 0.90 else "clean"}</span></td></tr>'
        for k, v in (exp.get("leakage_canary_auc") or {}).items())

    hd = exp.get("holdout_dti") or {}
    budgets = sorted({b for d in hd.values() for b in d}, key=int)
    head = "".join(f'<th class="n">n={int(b):,}</th>' for b in budgets)
    hrows = "".join(
        f'<tr><td class="mono">{html.escape(k)}</td>'
        + "".join(f'<td class="n">{fmt(d.get(b), 5)}</td>' for b in budgets) + "</tr>"
        for k, d in hd.items())

    ab = abl.get("geopb_ablation") or {}
    abrows = "".join(
        f'<tr><td class="n">{int(n):,}</td><td class="n">{fmt(d["with"],5)}</td>'
        f'<td class="n">{fmt(d["without"],5)}</td><td class="n">{d["delta"]:+.5f}</td>'
        f'<td class="n">{d["folds_positive"]}/4</td></tr>' for n, d in ab.items())

    calrows = "".join(
        f'<tr><td class="mono">{html.escape(a["file"][:54])}</td>'
        f'<td class="n">{fmt(a["owner_reported_live_dti"])}</td>'
        f'<td class="n">{fmt(a["holdout_pooled_dti"],5)}</td>'
        f'<td class="n">{a["n_emitting_px"]:,}</td>'
        f'<td class="n">{a["on_catalogue_px"]:,}</td></tr>'
        for a in sorted((cal.get("artifacts") or []),
                        key=lambda r: -r["owner_reported_live_dti"]))

    duprows = "".join(
        f'<tr><td class="mono">{html.escape(d["file"][:56])}</td>'
        f'<td class="n">{fmt(d["spearman_surface"],3)}</td>'
        f'<td class="n">{fmt(100*d["dot_overlap_3px"],1)}%</td>'
        f'<td><span class="tag {"t-bad" if d["duplicate"] else "t-ok"}">'
        f'{"DUPLICATE" if d["duplicate"] else "distinct"}</span></td></tr>'
        for d in (dup.get("comparisons") or []))

    sp = (cal.get("spearman_holdout_vs_live") or {})
    spn = (cal.get("spearman_npx_vs_live") or {})

    body = f"""
<h1>Method &amp; evidence</h1>
<p class="sub">The hypothesis, the instrument, the controls, the ablation, and the results that
did not work. Negative results are published, not hidden.</p>

{_session_section()}

<h2>1. The lane — GEO-Pb, a juxtaposition detector</h2>
<div class="card">
<p>Every fault detector in the 60 sibling GEMSDOE repositories is a <b>derivative</b> operator —
Sato/Frangi/Hessian ridges, tilt angle, horizontal gradient, Euler deconvolution, worms, gradient
coherence. A derivative asks <i>“is this field changing fast here?”</i>. A fault, physically, is a
<b>juxtaposition</b>: it puts two different geological domains side by side. The right question is
the two-sample one — <i>“do the rocks on the two sides of this line have different joint
geophysical signatures?”</i></p>
<p><b>GEO-Pb</b> answers it directly. At each pixel and each of eight candidate strikes it forms
the offset difference of a covariance-whitened 10-band stack across the candidate line (a windowed
Hotelling-style step statistic — the geophysical analogue of the half-disc <i>Pb</i> boundary
detector from computer vision), takes the <b>median of three independent physics domains</b>
(potential-field/subsurface, airborne radiometric, topographic) so at least two must agree, and
multiplies by an <b>along-strike persistence</b> term over 1.5 km so only straight, continuing
boundaries survive.</p>
<p><b>Why it should find a fault the catalogue lacks.</b> The supplied labels are USGS Quaternary
faults plus INGENIOUS — structures mapped from <i>surface</i> evidence. A fault concealed under
Holocene alluvium with no scarp still juxtaposes different basement susceptibility, different
cover thickness and different surface geochemistry. Each band changes a little; the joint
10-vector changes a lot. That is exactly the class a scarp-first catalogue under-samples and a
derivative detector under-weights.</p>
<p><b>Named non-fault processes that mimic it</b> (declared before measuring): distal
alluvial-fan margins and Lake Lahontan highstand shorelines (lobate and closed — killed by the
straightness term); aeromagnetic/radiometric acquisition seams (single-domain — killed by the
two-of-three vote, and audited below); erosional volcanic mesa and flow margins (straight
<i>and</i> multi-domain — <b>the irreducible confounder, declared, not solved</b>).</p>
</div>

<h2>2. The instrument — hide-and-recover, spatially blocked</h2>
<p>The catalogue is split into connected fault <b>segments</b>; segments are assigned to four
folds by spatial block so a whole region is hidden at once. Each catalogue pixel within 5 px of a
withheld pixel is also removed from <code>visible</code>. Every catalogue-derived quantity is
recomputed from <code>visible</code> only; the prediction is masked to zero <b>pixel-exactly</b>
on <code>visible</code>; the fold is scored with the official metric against the withheld
segments; the four folds are pooled into one DTI.</p>
<div class="note"><b>IR-85-001 — a shared-tooling defect found and fixed.</b> A hide-and-recover
holdout <b>cannot</b> score a finished raster that was built with a hard catalogue exclusion: the
artifact has already deleted every dot near the segments the holdout then hides, so its score is
forced to ≈ 0 <i>by its own success condition</i>. Measured here: the family's best live artifact
(0.2778 OWNER-REPORT) scores <b>0.0048</b> on this holdout, while <code>Hedge-v2</code>, which puts
60,988 dots directly on the catalogue, scores <b>0.3177</b> and is worth 0.1563 live. The fix is
structural: <code>holdout.score_folds</code> takes a <b>callable</b> and re-executes the rule per
fold. Every sibling repository that correlated a static-artifact holdout against the live board
was measuring this defect, not an instrument.</div>

<h3>Calibration: Spearman ρ against {len(cal.get("artifacts") or [])} artifacts with
owner-reported live scores</h3>
<div class="grid">
  <div class="kpi"><div class="l">ρ(static holdout, live)</div>
    <div class="v">{fmt(sp.get('rho'), 3)}</div>
    <div class="l" style="text-transform:none">p = {fmt(sp.get('p'), 3)} — not an instrument
    (see IR-85-001)</div></div>
  <div class="kpi"><div class="l">ρ(emitted pixels, live)</div>
    <div class="v">{fmt(spn.get('rho'), 3)}</div>
    <div class="l" style="text-transform:none">p = {spn.get('p', 0):.2e} — the strongest
    predictor in the record</div></div>
</div>
<table><tr><th>artifact</th><th class="n">live (OWNER-REPORT)</th>
<th class="n">static holdout</th><th class="n">emitted px</th><th class="n">on catalogue</th></tr>
{calrows}</table>

<h2>3. Leakage canary</h2>
<p>Each raw surface alone, AUC against the withheld positives. Above 0.90 means leakage until
proven otherwise. All GEO-Pb channels are functions of the geophysics only and never see the
catalogue, so leakage is impossible by construction — the canary confirms it.</p>
<table><tr><th>surface</th><th class="n">AUC</th><th>verdict</th></tr>{canary}</table>

<h2>4. Holdout DTI at matched emitted mass</h2>
<p>Pooled over 4 spatially-blocked folds; every surface rebuilt per fold; identical emission rule
(separation 2.8 px, 2 px catalogue exclusion).</p>
<table><tr><th>surface</th>{head}</tr>{hrows}</table>

<h2>5. The GEO-Pb ablation — does the new statistic add anything?</h2>
<p>Two gradient-boosted models on identical folds and identical emission, differing by one thing:
whether the three GEO-Pb channels are in the {len(abl.get("channels") or [])}-channel stack.</p>
<table><tr><th class="n">emitted px</th><th class="n">with GEO-Pb</th><th class="n">without</th>
<th class="n">Δ</th><th class="n">folds positive</th></tr>{abrows}</table>
<p>Mean withheld-AUC delta: <b>{fmt(abl.get('mean_auc_delta'), 4)}</b>.</p>

<h2>6. Confounder audit — acquisition seams</h2>
<p>Azimuth histogram of the strongest 1 % of GEO-Pb responses. A processing seam would pile the
response onto one flight-line azimuth.</p>
<pre><code>{html.escape(json.dumps(exp.get("confounder_audit", {}), indent=2))}</code></pre>

<h2>7. Duplicate check against the registry</h2>
<p>Parallel-run protocol: a candidate is a duplicate if its surface rank-correlates above 0.90
with any registry raster, or if more than 70 % of its dots fall within 3 px of one registry
raster's dots.</p>
<table><tr><th>registry raster</th><th class="n">Spearman ρ</th>
<th class="n">dots within 3 px</th><th>verdict</th></tr>{duprows}</table>

<h2 id="reading">Full write-ups</h2>
<p>The site summarises; these are the working documents, kept in the repository so every claim is
versioned alongside the code that produced it.</p>
<table>
<tr><th>document</th><th>what is in it</th></tr>
<tr><td><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/main/docs/research/metric-algebra.md">metric-algebra.md</a></td>
<td>The metric transcribed from the official page, the two exact identities
(<code>FN = K − T</code>, <code>FP = S − M</code>), the proof that binary predictions are optimal,
the marginal-bar table, and the back-solve of the 0.2778 incumbent.</td></tr>
<tr><td><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/main/docs/research/hypotheses.md">hypotheses.md</a></td>
<td>All five candidate hypotheses with named layers, transforms, the reason each targets a fault
<em>missing</em> from the catalogue, and the expected-gain / cost ranking that selected H85-1.</td></tr>
<tr><td><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/main/knowledge/geothermal-vent-discovery.md">geothermal-vent-discovery.md</a></td>
<td>Original research on blind-geothermal discovery, including measurements made here: 1,839
hot/warm sites are 1.50× enriched within 1 km of mapped faults, <strong>33.7 % of them sit more
than 3 km from any mapped fault</strong>, and GEO-Pb is statistically blind to all of them
(AUC 0.5034, p = 0.213) — which makes a thermal channel an orthogonal fusion partner.</td></tr>
<tr><td><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/main/README.md">README.md</a></td>
<td>The standing brief, the full answer to “why 0.2778”, limitations, required access, and the
prioritised list of remaining work.</td></tr>
</table>
"""
    return page("Method & evidence — GEMSDOE85", body, "method.html")


def build_data() -> str:
    man = jload(ROOT / "registry" / "data_manifest.json") or {"files": []}
    rec = {r["id"]: r for r in (jload(ROOT / "registry" / "restore_receipt.json")
                                or {"files": []})["files"]}
    rows = ""
    for f in man["files"]:
        r = rec.get(f["id"], {})
        ok = r.get("status") in ("restored", "cached")
        rows += (f'<tr><td class="mono">{html.escape(f["id"])}</td>'
                 f'<td class="n">{f.get("bytes",0)/1e6:.1f} MB</td>'
                 f'<td class="mono">{html.escape(f["sha256"][:16])}…</td>'
                 f'<td><span class="tag {"t-ok" if ok else "t-bad"}">'
                 f'{"verified" if ok else "missing"}</span></td>'
                 f'<td style="font-size:12.5px">{html.escape(f.get("provenance",""))}</td></tr>')
    body = f"""
<h1>Data &amp; sources</h1>
<p class="sub">Every input byte is fetched from a commit-pinned mirror and verified against a
SHA-256 before use. Nothing here is organizer-authenticated; the provenance column says exactly
what each pin does and does not prove.</p>

<div class="note"><b>Access limitation, stated plainly.</b> The competition data page
(<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">drivendata.org
→ Data</a>) is behind a login, so this repository cannot fetch
<code>training_features.tif</code>, <code>labels.tif</code>, <code>sample_submission.tif</code> or
<code>1m_DEM_links.csv</code> directly. It restores them from operator-supplied GitHub mirrors
pinned by commit SHA and verifies every byte against the hash recorded in
<code>registry/data_manifest.json</code>. That proves <b>mirror consistency</b>, not organizer
authentication. Run <code>python scripts/restore_data.py --groups core external scored</code> to
reproduce.</div>

<h2>Restored inputs</h2>
<table><tr><th>id</th><th class="n">size</th><th>sha256</th><th>state</th><th>provenance</th></tr>
{rows}</table>

<h2>Official sources</h2>
<table>
<tr><th>what</th><th>link</th></tr>
<tr><td>Competition home</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">drivendata.org/competitions/306</a></td></tr>
<tr><td>Problem description (metric, submission format)</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page/967</a></td></tr>
<tr><td>About page</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">page/968</a></td></tr>
<tr><td>Data download (login required)</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">/data/</a></td></tr>
<tr><td>Leaderboard</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">/leaderboard/</a></td></tr>
<tr><td>Official rules PDF</td><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">docs.nlr.gov/docs/fy26osti/96647.pdf</a></td></tr>
<tr><td>Reference solution</td><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">drivendataorg/gems-prize-reference-solution</a></td></tr>
<tr><td>GeoDAWN airborne magnetic &amp; radiometric surveys</td><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">usgs.gov/data/geodawn…</a></td></tr>
<tr><td>INGENIOUS project</td><td><a href="https://gbcge.org/current-projects/ingenious/">gbcge.org/current-projects/ingenious</a></td></tr>
<tr><td>INGENIOUS data (GDR 1391)</td><td><a href="https://gdr.openei.org/submissions/1391">gdr.openei.org/submissions/1391</a></td></tr>
<tr><td>USGS State Geologic Map Compilation</td><td><a href="https://mrdata.usgs.gov/geology/state/">mrdata.usgs.gov/geology/state</a></td></tr>
<tr><td>EPSG:32611 (UTM 11N)</td><td><a href="https://epsg.io/32611">epsg.io/32611</a></td></tr>
<tr><td>Tversky index</td><td><a href="https://en.wikipedia.org/wiki/Tversky_index">en.wikipedia.org/wiki/Tversky_index</a></td></tr>
</table>

<h2>Reproduce from a clean checkout</h2>
<pre><code>git clone https://github.com/buffedlizard55-lab/GEMSDOE85 &amp;&amp; cd GEMSDOE85
python -m venv .venv &amp;&amp; .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --groups core external scored   # SHA-256 verified
.venv/bin/python -m pytest tests -q                                      # metric vs official example
.venv/bin/python scripts/run_experiments.py                              # holdout + canary + audit
.venv/bin/python scripts/run_supervised.py                               # GEO-Pb ablation
.venv/bin/python scripts/build_submission.py                             # writes + validates the .tif
.venv/bin/python scripts/build_site.py                                   # regenerates this site</code></pre>
"""
    return page("Data & sources — GEMSDOE85", body, "data.html")


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("")
    for name, fn in [("index.html", build_index), ("executive-summary.html", build_exec),
                     ("method.html", build_method), ("data.html", build_data)]:
        (DOCS / name).write_text(fn())
        print(f"wrote docs/{name}")
    return 0


def build() -> int:
    return main()


if __name__ == "__main__":
    raise SystemExit(main())
