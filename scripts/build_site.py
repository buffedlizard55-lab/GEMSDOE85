#!/usr/bin/env python3
"""Build an evidence-driven, blocked release portal, not a slot selector.

Always recompute the local audit. Historical evidence is retained, never promoted
because it passed format checks. No model or private shared-tool fork lives here.
"""
from __future__ import annotations
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from release_audit import audit

BANNER = 'BLOCKED — DO NOT SUBMIT'
ARCHIVE_START = '<!-- current-release-status -->'
ARCHIVE_END = '<!-- /current-release-status -->'
STYLE = '''body{margin:0;background:#0d1117;color:#e6edf3;font:16px/1.65 system-ui,sans-serif}
main,nav{max-width:1040px;margin:auto;padding:24px}nav{display:flex;gap:24px;flex-wrap:wrap}
a{color:#79b8ff}h1{line-height:1.2}h2{margin-top:40px}code{overflow-wrap:anywhere}
.hero{border:2px solid #f0b35b;background:#281f13;border-radius:14px;padding:24px}
.card{background:#161b22;border:1px solid #30363d;padding:20px;border-radius:12px;margin:18px 0}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border:1px solid #30363d;text-align:left;overflow-wrap:anywhere}
.scroll{overflow:auto}small,.muted{color:#aeb9c6}pre{white-space:pre-wrap;overflow-wrap:anywhere}
button{padding:12px}footer{border-top:1px solid #30363d;margin-top:40px;padding:20px 0}'''


def esc(value):
    return html.escape(str(value))


def page(title, body):
    links = [('index.html', 'Release status'), ('executive-summary.html', 'How submission works'),
             ('method.html', 'Science & research'), ('data.html', 'Evidence & sources'),
             ('artifacts.html', 'Historical diagnostics')]
    nav = ''.join(f'<a href="{url}">{label}</a>' for url, label in links)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · GEMSDOE85</title>
<style>{STYLE}</style></head><body><nav>{nav}</nav><main>
<section class="hero" data-release-status="blocked"><strong>{BANNER}</strong>
<p>No new TIFF has passed the required uniqueness, lane and holdout gates. Format validity alone is not clearance.
No weekly submission slot was used or selected.</p></section>
{body}<footer>AI-assisted research · DOE GEMS fault prediction is not proof of a geothermal vent or productive reservoir.
<a href="https://github.com/buffedlizard55-lab/GEMSDOE85">Source repository</a> ·
<a href="evidence/run_card.json">Current machine-readable run card</a></footer></main></body></html>'''


def index(card):
    blockers = ''.join(f'<li>{esc(s)}</li>' for s in card['blockers'])
    sat = card['registry'].get('saturation_certificate') or {}
    overlap = sat.get('covered_allowed_fraction', 'not locally verified')
    return page('Submission release status', f'''
<h1>Is there a TIFF I can download and submit?</h1>
<p><strong>No cleared new submission is available.</strong> Existing TIFFs are historical research artifacts,
not newly generated submissions. The project checks release prerequisites automatically; it does not require a visual inspector.</p>
<div class="card"><h2>Why release stopped</h2><ul>{blockers}</ul></div>
<p><b>REGISTRY-MEASUREMENT, not a score:</b> the pinned dense-prior witness covers {esc(overlap)} of the allowed domain
within the protocol's three-pixel neighborhood. Every nonempty candidate overlaps this witness above the literal gate.
This blocks the pre-placement surface stage; no new dots were placed.</p>
<p><a href="executive-summary.html">Executive summary and exact conditional submission steps →</a><br>
<a href="artifacts.html">Historical TIFF byte-level format diagnostics →</a></p>
<h2>What this review delivered</h2><ul>
<li>One fail-closed release decision shared by the site, audit and CI.</li>
<li>On-disk validation with the unchanged pinned shared validator, including exact reference transform.</li>
<li>Research candidates and a conservative H33 explanation, with claims separated from measurements.</li>
<li>A negative preflight run card. No geological experiment was run; no performance improvement is claimed.</li></ul>
<p>Inherited cards claiming promotion remain historical evidence only. A restricted registry or a chance-corrected overlap
rule cannot silently replace the user's any-registry-raster rule.</p>''')


def executive():
    return page('Executive summary', '''
<h1>Executive summary: submission is currently blocked</h1>
<p>There is no approved file name or submission note for a new candidate. Do not upload an archived TIFF to satisfy this run.</p>
<h2>Automated release checklist</h2><ol>
<li>Record an explicit method lane and obtain the pinned template cache. Do not rebuild a private substitute.</li>
<li>Resolve the dense-prior protocol conflict in a versioned policy decision. Until then the literal gate stops every nonempty candidate.</li>
<li>Check surface uniqueness against the registry before placement. Run feature-alone leakage canaries.</li>
<li>Use the shared hide-and-recover evaluator: whole buffered segments, fold-visible catalogue features,
pixel-exact known-fault masking, pooled metric terms and paired spatial-cluster confidence intervals.</li>
<li>Beat the current incumbent on identical folds; then check final-dot uniqueness.</li>
<li>Use the shared writer; reopen the file and verify one float32 band, exact sample CRS, shape and transform,
finite [0,1] values, zero exterior and a unique hash/name with a note no longer than 140 characters.</li>
<li>Publish a one-click TIFF download only after those gates clear. Slot selection remains separate.</li></ol>
<h2>Exactly how to submit once clearance exists</h2><ol>
<li>Download the cleared single-band <code>.tif</code>, or a ZIP containing exactly that TIFF. Match its displayed SHA-256.</li>
<li>Sign in and join the competition at the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData submissions page</a>.</li>
<li>Check the remaining weekly quota and rules, then use “New submission” → “File to submit”.</li>
<li>Select the cleared TIFF; paste its generated short note. A selector—not this site—authorizes use of the slot.</li>
<li>Upload, and record the file hash and submission-page receipt. Only a score from that receipt is ORGANIZER-CONFIRMED.</li></ol>
<h2>The prior [0,1] rejection</h2>
<p>The error alone does not identify its cause. Negative nodata sentinels, nonfinite values or actual values outside [0,1]
are possibilities, not a diagnosis. The conservative export policy checks every stored pixel and avoids NaN exterior margins.
This is a local format check, not a guarantee of organizer acceptance. No human inspection substitutes for these gates.</p>
<p>The current account-specific weekly quota and live leaderboard are not verified in this environment.</p>''')


def science():
    return page('Science and research', '''
<h1>Scientific assessment and ranked next tests</h1>
<h2>Why H33 may have worked</h2>
<p>The reported 0.2778 is OWNER-REPORTED / NOT RECEIPT-VERIFIED, not ORGANIZER-CONFIRMED.
H33's sparse binary support reduces prediction mass; spacing can reduce redundant coverage under a max-cover metric.
Removing uncredited mass can improve a Tversky ratio if captured truth credit remains unchanged. Whether that occurred on
hidden labels cannot be established from a published TIFF or from two scores alone.</p>
<p>We cannot identify the private truth mass, attribute a causal gain to pruning, prove binary probabilities are globally optimal,
or promise a score above the owner's reported value. The brief also gives inconsistent leaderboard targets; neither is a fresh receipt.</p>
<p><a href="research/session-df29b0af-review.md">Current research review, hypotheses and evidence boundaries</a> ·
<a href="research/why-h33.md">Earlier conservative H33 analysis</a></p>
<h2>Ranked hypotheses — proposals, not an assigned lane</h2>
<p>Qualitative priority and cost only: no projected scores. All require the same strict preflight and holdout before a slot.</p>
<div class="scroll"><table><tr><th>Priority / cost</th><th>Hypothesis and supplied layers</th><th>Signature / missing-fault rationale</th><th>Named mimic</th></tr>
<tr><td>First / medium</td><td>Signed paired basin-interface profiles: basement-depth proxy, gravity, terrain controls</td><td>Ordered flank offset and gravity curvature rather than unsigned boundary magnitude; targets buried steps</td><td>Sedimentary facies / erosional basement relief</td></tr>
<tr><td>Second / medium–high</td><td>Cross-scale magnetic edge displacement: RTP, TMI, depth proxy, relief</td><td>Consistent lateral shift of an edge across scales in subdued terrain; tests concealed continuation</td><td>Intrusive contact / remanence / acquisition geometry</td></tr>
<tr><td>Third / high</td><td>Cross-drainage residual facet offsets: detrended elevation and slope</td><td>Repeated signed offsets across independent drainages, not one ridge or slope maximum</td><td>Lahontan shoreline / resistant bedding</td></tr>
<tr><td>Fourth / medium</td><td>Negative-control fan-front rejection: terrain, radiometric and magnetic domains</td><td>Reject radial fan margins while preserving throughgoing discordant boundaries; improves precision if valid</td><td>Tectonic fan-front truncation (a real fault wrongly rejected)</td></tr></table></div>
<p>These are research variants, not proven globally novel methods. The first three refine previously proposed but unexecuted
shortlists. No implementation of their specific signed/profile controls was found in the inspected detector code; broad related
boundary, worm, radiometric, terrain and supervised methods already exist. Full cross-repository novelty remains unverified.</p>
<p>No new external dataset is assumed obtainable. USGS/DOE source URLs are provided for review, but official-host access is restricted here.</p>
<h2>Geothermal inference boundary</h2><p>Fault prediction does not establish a vent, heat source, permeability or commercially usable flow.
The historical knowledge note contains unverified and overstrong claims; use the current review's corrections before reuse.</p>''')


def sources():
    return page('Evidence and sources', '''
<h1>Evidence and official-source access</h1>
<ul><li><a href="evidence/run_card.json">Current run card and per-file validation</a></li>
<li><a href="registry/template_pin.json">Unchanged shared-tool hashes</a></li>
<li><a href="registry/learning_manifest.json">Pinned educational H33 and saturation-witness bytes</a></li>
<li><a href="registry/lane.json">Lane assignment status</a> · <a href="registry/cache_manifest.json">Cache availability</a></li>
<li><a href="registry/irregularities.json">Irregularities and corrections</a></li>
<li><a href="evidence/source_review_df29b0af.json">This session's source verification receipt</a></li></ul>
<div class="scroll"><table><tr><th>Source</th><th>What is verified this session</th></tr>
<tr><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b">Organizer reference, pinned commit</a></td><td>README and notebook fetched via GitHub. CPU option exists; notebook uses U-Net and Tversky loss with alpha 0.2 / beta 0.8. This is training loss, not our holdout certificate.</td></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official task and format</a></td><td>Linked for review. Not freshly fetched in this restricted session; earlier retrieval claims remain historical.</td></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Official competition data</a></td><td>No authenticated data download. Local sample and catalogue match owner-mirror hash pins, not organizer authentication.</td></tr>
<tr><td><a href="https://doi.org/10.5066/P93LGLVQ">USGS GeoDAWN</a> · <a href="https://gdr.openei.org/submissions/1391">DOE GDR</a> · <a href="https://mrdata.usgs.gov/geology/state/">USGS SGMC</a></td><td>Cited official sources; reachability, licenses and new downloads not verified here. Do not infer eligibility from agency ownership alone.</td></tr>
<tr><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Rules PDF</a></td><td>Not fetched here. Account quota and rules acceptance unknown. No submission selected or uploaded.</td></tr></table></div>
<p>All performance in earlier run cards is historical local HOLDOUT-DTI or unverified owner reports. Different instruments cannot be ranked
against each other. The current card has no DTI value, withheld count or confidence interval because no experiment ran.</p>''')


def artifacts(card):
    rows = []
    for row in card['historical_artifacts']:
        name = row['file']
        label = esc(name)
        if name.startswith('docs/'):
            label = f'<a href="{esc(name[5:])}">{label}</a>'
        rows.append(f'<tr><td>{label}<br><small>{esc(row["sha256"])}</small></td>'
                    f'<td>{"PASS" if row["format_ok"] else "FAIL / NOT VERIFIED"}</td><td>BLOCKED</td></tr>')
    return page('Historical byte diagnostics', '''<h1>Historical artifacts — education only, do not submit</h1>
<p>These bytes predate this run. They are not unique new submissions. Download links below are for reproducibility and learning only.
A conservative format PASS does not pass the literal uniqueness gate or approve a weekly slot. NaN-outside variants fail our all-finite export policy.</p>
<div class="scroll"><table><tr><th>Artifact / SHA-256</th><th>Format diagnostic</th><th>Release</th></tr>''' + ''.join(rows) + '</table></div>')


def build(root=ROOT):
    root = Path(root)
    docs = root / 'docs'
    docs.mkdir(exist_ok=True)
    card = audit(root)
    if card.get('safe_to_submit') is not False or card.get('verdict') != 'negative':
        raise RuntimeError('This review portal cannot authorize promotion; implement an independently tested selector first')
    (root / 'evidence/run_card.json').write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
    pages = {'index.html': index(card), 'executive-summary.html': executive(),
             'method.html': science(), 'data.html': sources(), 'artifacts.html': artifacts(card)}
    for name, text in pages.items():
        (docs / name).write_text(text)
    # Mark ALL legacy entry points before any old claim/download can be interpreted as current approval.
    for path in sorted(docs.rglob('*.html')):
        if path.parent == docs and path.name in pages:
            continue
        text = path.read_text()
        text = re.sub(re.escape(ARCHIVE_START) + r'.*?' + re.escape(ARCHIVE_END), '', text, flags=re.S)
        link = Path(os.path.relpath(docs / 'index.html', path.parent)).as_posix()
        notice = (ARCHIVE_START + f'<aside data-release-status="blocked" style="padding:24px;background:#3b240c;color:white;position:relative;z-index:9999">'
                  f'<strong>{BANNER}</strong> — Historical page; all older approval/download claims below are superseded. '
                  f'<a style="color:white" href="{link}">Current release decision</a></aside>' + ARCHIVE_END)
        text = re.sub(r'(<body\b[^>]*>)', lambda m: m.group(1) + notice, text, count=1, flags=re.I)
        path.write_text(text)
    (root / 'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=docs/index.html"><title>GEMSDOE85 status</title></head>'
        f'<body data-release-status="blocked"><h1>{BANNER}</h1><a href="docs/index.html">Current release status and evidence</a></body></html>\n')
    for group in ('evidence', 'registry'):
        (docs / group).mkdir(exist_ok=True)
        for source in sorted((root / group).glob('*.json')):
            shutil.copyfile(source, docs / group / source.name)
    shutil.copyfile(root / 'evidence/run_card.json', docs / 'downloads/run_card.json')
    for name in ('session-df29b0af-review.md', 'why-h33.md'):
        shutil.copyfile(root / 'research' / name, docs / 'research' / name)
    return 0


if __name__ == '__main__':
    raise SystemExit(build())
