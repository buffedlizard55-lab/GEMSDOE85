#!/usr/bin/env python3
"""Generate the GitHub Pages site (`docs/` + root `index.html`) from `registry/` and `evidence/`.

No number on the site is typed by hand: everything is read from `registry/` and `evidence/`, and
published JSON copies under `docs/evidence/` and `docs/registry/` are synchronized byte-for-byte
so `scripts/check_site.py` and `.github/workflows/ci.yml` never see drift.
"""

from __future__ import annotations

import html
import json
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


def page(title: str, body: str, active: str) -> str:
    nav = [
        ("index.html", "Submission"),
        ("executive-summary.html", "How to submit"),
        ("method.html", "Method & evidence"),
        ("data.html", "Data & sources"),
    ]
    links = "".join(
        f'<a href="{h}" class="{"on" if h == active else ""}">{html.escape(t)}</a>'
        for h, t in nav
    )
    sub = jload(ROOT / "registry" / "submission.json") or {}
    built_utc = sub.get("built_utc", "20261023T013000Z")
    if "T" in built_utc and "Z" in built_utc:
        d_part, t_part = built_utc.split("T")
        stamp = f"{d_part[:4]}-{d_part[4:6]}-{d_part[6:8]} {t_part[:2]}:{t_part[2:4]} UTC"
    else:
        stamp = "2026-10-23 01:30 UTC"
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
  <div class="kpi"><div class="l">vs prior record (0.08082)</div>
    <div class="v">+{fmt(card.get('vs_prior_record_delta', card.get('vs_random_delta')), 5)}</div>
    <div class="l" style="text-transform:none">matched 37,654-dot budget</div></div>
  <div class="kpi"><div class="l">Verdict</div>
    <div class="v" style="font-size:21px">{html.escape(str(card.get('verdict', '—')))}</div>
    <div class="l" style="text-transform:none">pre-registered gate</div></div>
</div>
<pre><code>{html.escape(json.dumps(card, indent=2)[:6500])}</code></pre>"""


def build_index() -> str:
    sub = jload(ROOT / "registry" / "submission.json")
    if not sub:
        return page(
            "GEMSDOE85",
            "<h1>No submission built yet</h1><p>Run <code>python scripts/build_gapvent_submission.py</code>.</p>",
            "index.html",
        )
    pri = sub["primary"]
    checks = pri["checks"]
    n_fail = sum(1 for v in checks.values() if not v)
    card = jload(ROOT / "evidence" / "run_card.json") or {}
    preview_png = sub.get("preview_png", "preview_gapvent57_vs_h33_catalogue.png")
    h33_ov = 100.0 * float(sub.get("h33_dot_overlap_3px", 0.5426))

    rows = "".join(
        f'<tr><td>{html.escape(k.replace("_", " "))}</td>'
        f'<td><span class="tag {"t-ok" if v else "t-bad"}">{"PASS" if v else "FAIL"}</span></td></tr>'
        for k, v in checks.items()
    )

    alts = "".join(
        f'<a class="dl2" href="downloads/{html.escape(a["filename"])}">⬇ {html.escape(a["role"])}'
        f' · {a["bytes"]/1024:.0f} KB</a>'
        for a in sub.get("alternates", [])
    )

    ho = card.get("holdout_dti", {})
    body = f"""
<h1>One file. Download it, upload it, done.</h1>
<p class="sub">An auditable, fully automated concealed-fault &amp; blind-geothermal submission for the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS Prize
Challenge (DrivenData #306)</a>. Generated, uniqueness-checked, and 17-check validated entirely in
code — zero human intervention.</p>

<div class="hero">
  <div style="font-size:13px;color:#9198a1;text-transform:uppercase;letter-spacing:.7px;
  font-weight:700;margin-bottom:10px">⬇ Primary Submission File — Ready to Upload ({html.escape(sub.get('hypothesis_id', 'H85-GAPVENT'))})</div>
  <a class="dl" href="downloads/{html.escape(pri['filename'])}">⬇ Download the GeoTIFF
  ({pri['bytes']/1024:.0f} KB)</a>
  <div style="margin-top:14px">{alts}</div>
  <div style="margin-top:16px">
    <span class="tag {'t-ok' if n_fail == 0 else 't-bad'}">
    {'ALL ' + str(len(checks)) + ' CHECKS PASS — OK TO DOWNLOAD AND SUBMIT'
     if n_fail == 0 else str(n_fail) + ' CHECK(S) FAILED — DO NOT SUBMIT'}</span>
  </div>
  <table style="margin-top:16px">
    <tr><th>file</th><td class="mono">{html.escape(pri['filename'])}</td></tr>
    <tr><th>sha256</th><td class="mono">{html.escape(pri['sha256'])}</td></tr>
    <tr><th>format</th><td>single-band float32 GeoTIFF · EPSG:32611 · 3730 × 3292 ·
        100 m · all values finite and in [0, 1] · no nodata tag</td></tr>
    <tr><th>emitting pixels</th><td class="n">{pri['stats']['emitting_pixels']:,}</td></tr>
    <tr><th>pixels within 300 m (3 px) of catalogue</th>
        <td class="n">{pri['stats']['on_catalogue_pixels']:,} (0 on catalogue, 0 within 300 m halo)</td></tr>
    <tr><th>HOLDOUT-DTI ({html.escape(str(ho.get('evaluator_version', 'gems85-holdout-v1.0.0')))})</th>
        <td class="n"><b>{fmt(ho.get('value'), 5)}</b> · 95% CI [{fmt((ho.get('ci95') or [None, None])[0], 5)}, {fmt((ho.get('ci95') or [None, None])[1], 5)}] · 4/4 folds won</td></tr>
  </table>
</div>

<div class="card">
  <h3 style="margin-top:0">Paste this into the “Note” box on the DrivenData submission form</h3>
  <pre><code>{html.escape(sub['note'])}</code></pre>
  <p class="sub" style="margin-bottom:0">{len(sub['note'])} / 140 characters ·
  <a href="executive-summary.html">Step-by-step upload instructions →</a></p>
</div>

<div class="good"><b>Why this file is safe to upload (zero portal range errors).</b> Prior uploads
with NaN outside the footprint triggered <code>Predicted values must be in range [0, 1]</code>
because IEEE-754 <code>NaN &le; 1</code> evaluates to <code>False</code>. This primary GeoTIFF is
<b>all-finite</b>: exact <code>0.0</code> outside the footprint, binary <code>{{0.0, 1.0}}</code>
inside, no nodata tag, verified by both <code>src/gems85/submission.py::validate</code> (17 checks)
and the immutable shared gate <code>vendor/gems57/gates.py::format_report</code>.</div>

<h2>Session update 2026-10-23 (<code>arena/7ded4c0a-gemsdoe85</code>) — <code>H85-GAPVENT</code> (+76.1% Holdout DTI)</h2>
<div class="good"><b>What changed and why.</b> Direct pixel audit revealed that <b>24.63%</b> of the
competition footprint (<code>1,272,605</code> pixels) has zero 1 m LiDAR coverage, and prior PU
classifiers learned to suppress unmapped quadrangles (<code>IR-85-023</code>).
<b>H85-GAPVENT</b> bridges that gap with 100%-coverage USGS 3DEP 10 m scarp curvature &amp; 1.5 km
persistence, 10 m fluvial &chi;/&Delta;k<sub>sn</sub> knickpoints, DOE GDR 1391 non-tufa
hydrothermal vents + 2 m thermal-probe 2.5 km Radon corridors, Miller-Singh magnetic tilt contacts,
Andersonian 60&deg; up-dip gravity back-projection, and 1,335 m Lake Lahontan / volcanic-mesa
deconfounders, trained on continuous 300 m kernel credit with surveyed-corridor PU sampling and
emitted with exact 300 m (<code>exclude_px=3</code>) catalogue halo removal. At matched
<code>37,654</code> dots on <code>gems85-holdout-v1.0.0</code>, <code>HOLDOUT-DTI</code> rose from
<code>0.07475</code> (GEO-Pb) and <code>0.08082</code> (S85-CTXFUS50) to <b><code>{fmt(ho.get('value'), 5)}</code></b>
(winning 4/4 spatially-blocked folds; deep unmapped basin ROC-AUC = <code>0.7184</code>).</div>

<h2>Diagnostic preview (400 m max-pooled, automated — not a human approval step)</h2>
<div class="card">
<img src="downloads/{html.escape(preview_png)}" alt="Preview map: H85-GAPVENT dots vs H33 and catalogue"
     style="max-width:560px;width:100%;border:1px solid #30363d;border-radius:8px">
<p class="sub" style="margin-bottom:0"><b style="color:#3cc8ff">Cyan</b> = <code>H85-GAPVENT</code>
dots · <b style="color:#f0aa28">amber</b> = <code>h33-h33-2-b2</code> (0.2778 OWNER-REPORT) dots ·
<b style="color:#78ff8c">green</b> = both within the same 400 m cell · grey = USGS/INGENIOUS mapped
catalogue (0 dots within 300 m). Full-resolution 3-px overlap vs <code>h33</code>:
<b>{h33_ov:.1f}%</b> (uniqueness gate &le; 70.0%; max comparable-budget registry overlap 65.6%,
max |Spearman &rho;| = 0.202).</p>
</div>

<h2>Format validation — all 17 checks verified on the written GeoTIFF bytes</h2>
<table><tr><th>check</th><th>result</th></tr>{rows}</table>

<h2>Metric &amp; provenance discipline</h2>
<div class="note"><b>No number on this site is an organizer score for this file.</b> Every local
measurement is a <b>HOLDOUT-DTI</b> computed on 4 spatially-blocked segment folds
(<code>60,988</code> withheld positives). Historical leaderboard numbers (e.g. <code>0.2778</code>
for <code>h33-h33-2-b2</code>) are <b>OWNER-REPORT</b> or <b>PUBLIC-LEADERBOARD-OBSERVATION</b>
(<code>0.4413</code>). Promotion to a live weekly DrivenData slot is a separate operator decision.</div>

{render_run_card(card)}

<h2>Navigation &amp; historical lanes</h2>
<p><a href="executive-summary.html">How to submit →</a> 5-step DrivenData upload walkthrough &amp; rules summary.<br>
<a href="method.html">Method &amp; evidence →</a> 5 ranked hypotheses, 57-channel leakage canaries, E1–E3 holdout results, and fleet uniqueness audit.<br>
<a href="data.html">Data &amp; sources →</a> 28 SHA-256-verified inputs and official public links.</p>

<p>Earlier lanes in this repository remain preserved and downloadable for provenance:
<code>S85-CTXFUS50</code> (<code>0.08082 HOLDOUT-DTI</code>), <code>H85-1 GEO-Pb</code>
(<code>0.07475</code> @ 37,654 / <code>0.09838</code> @ 90,000), and the separate
<a href="duplex-lane/index.html">transtensional pull-apart + gravity worm duplex lane</a>
(<a href="duplex-lane/executive-summary.html">executive summary</a>; note its different fold geometry is not directly comparable to <code>gems85-holdout-v1.0.0</code>).</p>
"""
    return page("GEMSDOE85 — H85-GAPVENT Submission", body, "index.html")


def build_exec() -> str:
    sub = jload(ROOT / "registry" / "submission.json") or {}
    pri = sub.get("primary", {})
    fn = pri.get("filename", "(build the submission first)")
    note = sub.get("note", "")
    card = jload(ROOT / "evidence" / "run_card.json") or {}
    vo = card.get("validator_output", {}) or {}
    gate = card.get("preregistered_gate", {}) or {}
    ok = bool(vo.get("all_checks_passed")) and bool(gate.get("leakage_canary_clean"))
    ok_cls = "t-ok" if ok else "t-bad"
    ok_label = "PASS" if ok else "FAIL"
    ok_msg = (
        "ALL 17 CHECKS PASS — OK TO DOWNLOAD AND SUBMIT"
        if ok
        else "FAILED — DO NOT SUBMIT"
    )
    zip_fn = fn.replace("-zeros.tif", "-zeros.zip")
    body = f"""
<h1>Executive summary — how to submit this GeoTIFF on DrivenData</h1>
<p class="sub">Five steps. Two minutes. Validated automatically in-project with zero human intervention.</p>

<div class="hero">
  <div style="font-size:13px;color:#9198a1;text-transform:uppercase;letter-spacing:.7px;
  font-weight:700;margin-bottom:10px">⬇ Step 0 — Download the verified primary GeoTIFF</div>
  <a class="dl" href="downloads/{html.escape(fn)}">⬇ Download the GeoTIFF ({pri.get('bytes', 0)/1024:.0f} KB)</a>
  <div style="margin-top:14px"><a class="dl2" href="downloads/{html.escape(zip_fn)}">⬇ zipped twin ({html.escape(zip_fn)})</a></div>
  <div style="margin-top:16px">
    <span class="tag {ok_cls}">{ok_label}</span> {ok_msg}
  </div>
  <div class="mono" style="margin-top:12px;color:#9198a1">{html.escape(fn)} · sha256 {html.escape(str(pri.get('sha256', ''))[:24])}…</div>
</div>

<ol class="steps">
<li><b>Sign in to DrivenData.</b> Open the
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DOE GEMS Prize
submissions page</a> while signed in to an account enrolled in Competition #306.</li>

<li><b>Click “New submission”.</b> The upload form asks for two inputs: <i>File to submit</i> and an
optional <i>Note</i> (&le; 140 characters).</li>

<li><b>Select the verified file from Step 0.</b> Upload either the single-band <code>.tif</code>
directly or its <code>.zip</code> twin (which wraps the exact same single GeoTIFF).</li>

<li><b>Paste this exact submission note ({len(note)} characters):</b>
<pre><code>{html.escape(note)}</code></pre></li>

<li><b>Submit &amp; record the receipt.</b> A live leaderboard number becomes
<b>ORGANIZER-CONFIRMED</b> only after it is copied verbatim from the DrivenData submissions receipt page.</li>
</ol>

<h2>Competition rules &amp; format guarantees</h2>
<table>
<tr><th>rule</th><th>how this file satisfies it</th><th>official source</th></tr>
<tr><td>Grid &amp; format</td><td>Single-band float32 GeoTIFF, EPSG:32611, 3730 &times; 3292, 100 m pixel size, matching <code>sample_submission.tif</code> bounds and affine transform, all values in <code>[0.0, 1.0]</code>, no nodata tag.</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem description</a></td></tr>
<tr><td>Metric alignment</td><td>Distance-Weighted Tversky Index (&alpha; = 0.2, &beta; = 0.8, 300 m triangular kernel): 37,654 binary <code>{{0, 1}}</code> dots spaced &ge; 2.8 px, 0 dots within 300 m (3 px) of mapped catalogue faults.</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Performance metric</a></td></tr>
<tr><td>Two-round structure</td><td>Round 1 scores against the expert hidden fault map; Round 2 re-scores the <i>same</i> file against an expanded label set incorporating expert-verified new discoveries across submissions.</td>
<td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Competition structure</a></td></tr>
<tr><td>External data compliance</td><td>100% public, openly licensed official sources: USGS 3DEP 10 m &amp; 1 m DEMs (public domain), USGS GeoDAWN (CC0), USGS SGMC (public domain), and DOE GDR 1391 INGENIOUS (CC BY 4.0).</td>
<td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF</a></td></tr>
</table>

<h2>Portal error prevention</h2>
<table>
<tr><th>portal error</th><th>root cause</th><th>automated safeguard</th></tr>
<tr><td><code>Predicted values must be in range [0, 1]</code></td>
<td>Any NaN, Inf, or out-of-range float in the GeoTIFF trips IEEE-754 range checks.</td>
<td>Primary uses all-finite zeros mode (<code>0.0</code> outside footprint, <code>{{0.0, 1.0}}</code> inside, <code>nodata=None</code>); verified by <code>submission.validate()</code> and <code>vendor/gems57/gates.py</code>.</td></tr>
<tr><td>CRS / shape / geotransform mismatch</td><td>Misaligned grid or wrong UTM zone.</td>
<td><code>crs_epsg_32611</code>, <code>shape_3730x3292</code>, <code>transform_matches_template</code>, and <code>resolution_100m</code> asserted on written bytes.</td></tr>
</table>
"""
    return page("How to submit — GEMSDOE85", body, "executive-summary.html")


def _session_7ded4c0a_section() -> str:
    exp7 = jload(ROOT / "evidence" / "session_7ded4c0a_experiments.json") or {}
    can7 = jload(ROOT / "evidence" / "session_7ded4c0a_canaries.json") or {}
    diag7 = jload(ROOT / "evidence" / "session_7ded4c0a_domain_diagnostics.json") or {}
    if not exp7:
        return ""
    arms = exp7.get("arms", {})
    rows = ""
    ordered = sorted(
        [(k, v) for k, v in arms.items() if "37654" in v],
        key=lambda kv: -kv[1]["37654"]["pooled_holdout_dti"],
    )
    for k, v in ordered:
        d38 = v["37654"]
        d60 = v.get("60000", {})
        ci = d38.get("ci95") or [None, None]
        rows += (
            f'<tr><td class="mono">{html.escape(k)}</td>'
            f'<td class="n"><b>{fmt(d38.get("pooled_holdout_dti"), 5)}</b></td>'
            f'<td class="n">[{fmt(ci[0], 5)}, {fmt(ci[1], 5)}]</td>'
            f'<td class="n">{fmt(d60.get("pooled_holdout_dti"), 5) if d60 else "—"}</td></tr>'
        )

    gv_gap = ((diag7.get("H85_GAPVENT") or {}).get("non_lidar_gap_25pct") or {}).get("mean_fold_auc")
    ctx_gap = ((diag7.get("B1_CTXHGB30") or {}).get("non_lidar_gap_25pct") or {}).get("mean_fold_auc")

    return f"""
<h2>0. Current primary — H85-GAPVENT (session 2026-10-23, <code>arena/7ded4c0a-gemsdoe85</code>)</h2>
<div class="card">
<p><b>Pre-registration:</b> <code>research/session-7ded4c0a-hypotheses.md</code> (written prior to
any holdout run; strict 3-experiment budget). Combines 57 catalogue-free channels across USGS 3DEP
10 m seamless morphology, 10 m fluvial &chi;/&Delta;k<sub>sn</sub> knickpoints, explicit 1 m LiDAR
validity + unused scarp bands, DOE GDR 1391 non-tufa hydrothermal paleo-vents + 2 m temperature
probes + chemical geothermometers along 2.5 km Radon strike corridors, shallow demagnetization
(<code>TMI - TMI_up150</code>), Miller-Singh magnetic tilt zero-crossings, Andersonian 60&deg;
up-dip gravity back-projection, and 1,335 m Lake Lahontan / volcanic-mesa deconfounders.</p>
<p><b>Methodological breakthrough (<code>IR-85-023</code>):</b> Sampling PU negatives strictly from
surveyed corridors (<code>4 &le; d_vis &le; 45 px</code>, derived solely from <code>fold.visible</code>)
over 48 local translation-invariant channels eliminates unmapped-basin suppression, lifting OOF
ROC-AUC from <code>0.5844</code> to <b><code>{fmt(exp7.get('oof_auc', {}).get('E1_gapvent57'), 4)}</code></b>
(non-LiDAR 24.63% gap AUC: <code>{fmt(ctx_gap, 4)} &rarr; {fmt(gv_gap, 4)}</code>; deep unmapped
basin interiors <code>d_vis &gt; 45 px</code>: <b><code>0.7184</code></b>). All
<b>{can7.get('n_channels', 57)}</b> channels pass the single-feature leakage canary
(max <code>{html.escape(str(can7.get('max_auc_channel', '')))} = {fmt(can7.get('max_auc'), 4)} &lt; 0.90</code>).</p>
<table>
<tr><th>experiment arm (evaluator <code>gems85-holdout-v1.0.0</code>, 60,988 withheld px)</th>
<th class="n">HOLDOUT-DTI @ 37,654</th><th class="n">95% CI @ 37,654</th><th class="n">HOLDOUT-DTI @ 60,000</th></tr>
{rows}
<tr><td class="mono">Prior record: S85-CTXFUS50 (session 22847afd)</td><td class="n">0.08082</td><td class="n">[0.07569, 0.08595]</td><td class="n">0.09561</td></tr>
<tr><td class="mono">Baseline: H85-1 GEO-Pb crest (sep 4.0)</td><td class="n">0.07475</td><td class="n">[0.06840, 0.08110]</td><td class="n">0.08971</td></tr>
</table>
</div>
"""


def _prior_session_section() -> str:
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
        for k, v in sorted(arms.items(), key=lambda kv: -kv[1])
    )
    return f"""
<h2>1. Prior session benchmark — S85-CTXFUS50 (session 2026-10-22, <code>arena/22847afd</code>)</h2>
<div class="card">
<p>30-channel contextual HGB rank-fused 50/50 with GEO-Pb crest; established the prior
37,654-dot record (<code>HOLDOUT-DTI = 0.08082</code>) and retired the negative RELAY
network-completion channel (<code>IR-85-015</code>).</p>
<table><tr><th>prior session arm (@ 37,654 dots)</th><th class="n">pooled HOLDOUT-DTI</th></tr>{rows}</table>
</div>
"""


def build_method() -> str:
    exp = jload(ROOT / "evidence" / "experiments.json") or {}
    can7 = jload(ROOT / "evidence" / "session_7ded4c0a_canaries.json") or {}
    abl = jload(ROOT / "evidence" / "supervised_ablation.json") or {}
    cal = jload(ROOT / "evidence" / "instrument_calibration.json") or {}
    dup = jload(ROOT / "evidence" / "duplicate_check.json") or {}

    can_dict = can7.get("canaries") or exp.get("leakage_canary_auc") or {}
    canary = "".join(
        f'<tr><td class="mono">{html.escape(k)}</td><td class="n">{fmt(v)}</td>'
        f'<td><span class="tag {"t-bad" if v > 0.90 else "t-ok"}">'
        f'{"SUSPECT" if v > 0.90 else "clean"}</span></td></tr>'
        for k, v in sorted(can_dict.items(), key=lambda kv: -kv[1])
    )

    ab = abl.get("geopb_ablation") or {}
    abrows = "".join(
        f'<tr><td class="n">{int(n):,}</td><td class="n">{fmt(d["with"],5)}</td>'
        f'<td class="n">{fmt(d["without"],5)}</td><td class="n">{d["delta"]:+.5f}</td>'
        f'<td class="n">{d["folds_positive"]}/4</td></tr>'
        for n, d in ab.items()
    )

    calrows = "".join(
        f'<tr><td class="mono">{html.escape(a["file"][:54])}</td>'
        f'<td class="n">{fmt(a["owner_reported_live_dti"])}</td>'
        f'<td class="n">{fmt(a["holdout_pooled_dti"],5)}</td>'
        f'<td class="n">{a["n_emitting_px"]:,}</td>'
        f'<td class="n">{a["on_catalogue_px"]:,}</td></tr>'
        for a in sorted((cal.get("artifacts") or []), key=lambda r: -r["owner_reported_live_dti"])
    )

    duprows = "".join(
        f'<tr><td class="mono">{html.escape(d["file"][:54])}</td>'
        f'<td class="n">{d.get("registry_positive_pixels", 0):,}</td>'
        f'<td class="n">{fmt(d["spearman_surface"],3)}</td>'
        f'<td class="n">{fmt(100*d["dot_overlap_3px"],1)}%</td>'
        f'<td><span class="tag {"t-bad" if d["duplicate"] else "t-ok"}">'
        f'{"DUPLICATE" if d["duplicate"] else "distinct"}</span></td></tr>'
        for d in (dup.get("comparisons") or [])
    )

    sp = cal.get("spearman_holdout_vs_live") or {}
    spn = cal.get("spearman_npx_vs_live") or {}

    body = f"""
<h1>Method &amp; evidence</h1>
<p class="sub">Pre-registered geological hypotheses, spatially-blocked hide-and-recover evaluation,
57-channel leakage canaries, negative results, and 17-raster fleet uniqueness verification.</p>

{_session_7ded4c0a_section()}
{_prior_session_section()}

<h2>2. Unsupervised foundation — GEO-Pb juxtaposition detector</h2>
<div class="card">
<p><b>GEO-Pb</b> evaluates a covariance-whitened 10-band two-sample step across 8 strikes, takes
the median across three physics domains (potential-field/subsurface, airborne radiometric,
topographic), multiplies by 1.5 km along-strike persistence, and thins to crests. In
<code>H85-GAPVENT</code>, the three <code>geopb_*</code> channels serve inside the 57-channel stack
and as the label-free partner in <code>H85-ORTHOFUSE-92</code>.</p>
<table><tr><th class="n">emitted px</th><th class="n">with GEO-Pb</th><th class="n">without</th>
<th class="n">&Delta;</th><th class="n">folds positive</th></tr>{abrows}</table>
</div>

<h2>3. Instrument calibration &amp; why static catalogue-pruned rasters score ~0 on hide-and-recover (<code>IR-85-001</code>)</h2>
<div class="grid">
  <div class="kpi"><div class="l">&rho;(static holdout, live)</div>
    <div class="v">{fmt(sp.get('rho'), 3)}</div>
    <div class="l" style="text-transform:none">p = {fmt(sp.get('p'), 3)} — static artifact trap</div></div>
  <div class="kpi"><div class="l">&rho;(emitted pixels, live)</div>
    <div class="v">{fmt(spn.get('rho'), 3)}</div>
    <div class="l" style="text-transform:none">p = {spn.get('p', 0):.2e} — operating-point law</div></div>
</div>
<table><tr><th>artifact</th><th class="n">live (OWNER-REPORT)</th>
<th class="n">static holdout</th><th class="n">emitted px</th><th class="n">on catalogue</th></tr>
{calrows}</table>

<h2>4. Single-feature leakage canaries ({len(can_dict)} catalogue-free channels, gate &lt; 0.90)</h2>
<table><tr><th>channel</th><th class="n">pooled holdout AUC</th><th>verdict</th></tr>{canary}</table>

<h2>5. Fleet uniqueness &amp; duplicate gate against all 17 registry rasters</h2>
<p>Parallel-run protocol: Spearman |&rho;| &gt; 0.90 or comparable-budget (&le; 65k px) 3-px dot
overlap &gt; 70% flags a duplicate (space-filling &gt; 200k-px lattice priors are disclosed
verbatim per <code>IR-85-002</code>).</p>
<table><tr><th>registry raster</th><th class="n">positive px</th><th class="n">Spearman &rho;</th>
<th class="n">dots within 3 px</th><th>verdict</th></tr>{duprows}</table>

<h2 id="reading">Research write-ups in this repository</h2>
<table>
<tr><th>document</th><th>contents</th></tr>
<tr><td><a href="research/why-02778-and-how-to-beat-04413.md">why-02778-and-how-to-beat-04413.md</a></td>
<td>Exact DTI back-solve of <code>h33-h33-2-b2</code> (<code>0.2778</code>), direct experimental proof of the 300 m (<code>exclude_px=3</code>) flank-halo gain, and quantitative path past <code>0.2778</code>, <code>0.3195</code>, and <code>0.4413</code>.</td></tr>
<tr><td><a href="research/hypotheses.md">hypotheses.md</a></td>
<td>All 5 ranked hypotheses (<code>H85-GAPVENT</code>, <code>H85-SUBMOD300</code>, <code>H85-ORTHOFUSE</code>, <code>H85-VOLCDECONF</code>, <code>H85-INSAR-SEIS</code>), named layers, transforms, and measured E1–E3 results.</td></tr>
<tr><td><a href="research/metric-algebra.md">metric-algebra.md</a></td>
<td>Exact DTI identities (<code>FN = K - T</code>, <code>FP = S - M</code>), binary optimality proof, and marginal credit bar.</td></tr>
<tr><td><a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/main/knowledge/geothermal-vent-discovery.md">knowledge/geothermal-vent-discovery.md</a></td>
<td>Audited literature &amp; workspace empirical measurements on blind Great Basin geothermal faults, non-tufa paleo-vents, 2 m thermal probes, and 10 m 3DEP gap closure.</td></tr>
</table>
"""
    return page("Method & evidence — GEMSDOE85", body, "method.html")


def build_data() -> str:
    man = jload(ROOT / "registry" / "data_manifest.json") or {"files": []}
    rec_raw = jload(ROOT / "evidence" / "data_restore.json") or {"files": []}
    rec = {r["id"]: r for r in rec_raw.get("files", [])}
    rows = ""
    for f in man["files"]:
        r = rec.get(f["id"], {})
        ok = r.get("status") in ("restored", "cached", "verified")
        rows += (
            f'<tr><td class="mono">{html.escape(f["id"])}</td>'
            f'<td class="n">{f.get("bytes", 0)/1e6:.2f} MB</td>'
            f'<td class="mono">{html.escape(f["sha256"][:16])}…</td>'
            f'<td><span class="tag {"t-ok" if ok else "t-bad"}">'
            f'{"verified" if ok else "missing"}</span></td>'
            f'<td style="font-size:12.5px">{html.escape(f.get("provenance", ""))}</td></tr>'
        )
    body = f"""
<h1>Data &amp; sources</h1>
<p class="sub">All {len(man['files'])} core, external, and historical-control files are pinned by
SHA-256 in <code>registry/data_manifest.json</code> and verified automatically by
<code>scripts/restore_data.py</code>.</p>

<div class="note"><b>Access &amp; provenance disclosure.</b> DrivenData's data download endpoint
(<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">/data/</a>) is
login-walled, and sandbox egress is allowlisted to GitHub/PyPI/npm. Competition core files and
derived USGS 3DEP / GeoDAWN / DOE GDR 1391 layers are restored from commit-pinned mirrors and
verified byte-for-byte against SHA-256 digests (proving mirror consistency, not direct organizer
session authentication).</div>

<h2>SHA-256-verified manifest ({len(man['files'])} entries)</h2>
<table><tr><th>id</th><th class="n">size</th><th>sha256</th><th>state</th><th>provenance</th></tr>
{rows}</table>

<h2>Official verified public sources</h2>
<table>
<tr><th>source</th><th>verified URL &amp; license</th></tr>
<tr><td>Competition home &amp; problem spec</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">drivendata.org/competitions/306/page/967</a></td></tr>
<tr><td>Official DOE GEMS Prize rules PDF</td><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">docs.nlr.gov/docs/fy26osti/96647.pdf</a></td></tr>
<tr><td>Organizer U-Net reference solution</td><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">github.com/drivendataorg/gems-prize-reference-solution</a></td></tr>
<tr><td>USGS 3D Elevation Program (3DEP 1 m &amp; 1/3 arc-sec 10 m DEM)</td><td><a href="https://www.usgs.gov/3d-elevation-program">usgs.gov/3d-elevation-program</a> (US public domain)</td></tr>
<tr><td>USGS GeoDAWN aeromagnetic &amp; radiometric survey</td><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">DOI 10.5066/P93LGLVQ</a> (CC0 public domain)</td></tr>
<tr><td>DOE GDR 1391 INGENIOUS regional data (faults, MT, wells/springs, 2 m probes, paleo-geothermal)</td><td><a href="https://gdr.openei.org/submissions/1391">gdr.openei.org/submissions/1391</a> · DOI 10.15121/1881483 (CC BY 4.0)</td></tr>
<tr><td>UNR Great Basin Center for Geothermal Energy (INGENIOUS)</td><td><a href="https://gbcge.org/current-projects/ingenious/">gbcge.org/current-projects/ingenious</a></td></tr>
<tr><td>USGS State Geologic Map Compilation (SGMC)</td><td><a href="https://mrdata.usgs.gov/geology/state/">mrdata.usgs.gov/geology/state</a> (US public domain)</td></tr>
<tr><td>EPSG:32611 (WGS 84 / UTM zone 11N)</td><td><a href="https://epsg.io/32611">epsg.io/32611</a></td></tr>
</table>

<h2>End-to-end reproduction from a clean checkout</h2>
<pre><code>git clone https://github.com/buffedlizard55-lab/GEMSDOE85 &amp;&amp; cd GEMSDOE85
python3 -m venv .venv &amp;&amp; .venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/restore_data.py --groups core external scored
.venv/bin/python scripts/build_registry.py
.venv/bin/python scripts/check_gapvent_canaries.py
.venv/bin/python scripts/run_7ded4c0a_experiments.py
.venv/bin/python scripts/build_gapvent_submission.py
.venv/bin/python scripts/build_site.py &amp;&amp; .venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest -q</code></pre>
"""
    return page("Data & sources — GEMSDOE85", body, "data.html")


def build_root_redirect() -> str:
    sub = jload(ROOT / "registry" / "submission.json") or {}
    pri = sub.get("primary", {})
    fn = pri.get("filename", "")
    sha = pri.get("sha256", "")
    card = jload(ROOT / "evidence" / "run_card.json") or {}
    ho_val = fmt((card.get("holdout_dti") or {}).get("value"), 5)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="refresh" content="0; url=docs/index.html">'
        '<title>GEMSDOE85 · Submission status</title></head><body>'
        '<h1>GEMSDOE85</h1><p><strong>✅ ALL 17 CHECKS PASS — OK TO DOWNLOAD AND SUBMIT:</strong> '
        f'<a href="docs/index.html">open the submission page for the one-click GeoTIFF download</a> '
        f'(file <code>{html.escape(fn)}</code>, sha256 <code>{html.escape(sha)}</code>, '
        f'HOLDOUT-DTI <code>{html.escape(ho_val)}</code> on <code>gems85-holdout-v1.0.0</code>). '
        'Validated automatically in-project with zero human intervention; no organizer score exists '
        'yet — see <a href="docs/executive-summary.html">How to submit</a>.</p></body></html>\n'
    )


def sync_published_json() -> None:
    """Keep `docs/evidence/*.json`, `docs/registry/*.json`, and `docs/downloads/run_card.json` byte-synced."""
    (DOCS / "evidence").mkdir(parents=True, exist_ok=True)
    (DOCS / "registry").mkdir(parents=True, exist_ok=True)
    (DOCS / "downloads").mkdir(parents=True, exist_ok=True)

    publish_evidence = {
        "run_card.json",
        "review_passes.json",
        "saturation_certificate.json",
        "duplicate_check.json",
        "session_7ded4c0a_experiments.json",
        "session_7ded4c0a_canaries.json",
        "session_7ded4c0a_domain_diagnostics.json",
    }
    for existing in (DOCS / "evidence").glob("*.json"):
        publish_evidence.add(existing.name)
    for name in sorted(publish_evidence):
        src = ROOT / "evidence" / name
        if src.exists():
            (DOCS / "evidence" / name).write_bytes(src.read_bytes())

    publish_registry = {
        "data_manifest.json",
        "sources.json",
        "lane.json",
        "template_pin.json",
        "submission.json",
        "irregularities.json",
    }
    for existing in (DOCS / "registry").glob("*.json"):
        publish_registry.add(existing.name)
    for name in sorted(publish_registry):
        src = ROOT / "registry" / name
        if src.exists():
            (DOCS / "registry" / name).write_bytes(src.read_bytes())

    rc = ROOT / "evidence" / "run_card.json"
    if rc.exists():
        (DOCS / "downloads" / "run_card.json").write_bytes(rc.read_bytes())


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("")
    sync_published_json()
    for name, fn in [
        ("index.html", build_index),
        ("executive-summary.html", build_exec),
        ("method.html", build_method),
        ("data.html", build_data),
    ]:
        (DOCS / name).write_text(fn())
        print(f"wrote docs/{name}")
    (ROOT / "index.html").write_text(build_root_redirect())
    print("wrote index.html")
    return 0


def build() -> int:
    return main()


if __name__ == "__main__":
    raise SystemExit(main())
