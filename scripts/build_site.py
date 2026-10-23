#!/usr/bin/env python3
"""Deterministic, fail-closed review portal. Does not select or upload submissions.

Historical format receipts are diagnostics, never authorization. A future promotion
publisher must independently verify scientific/uniqueness gates and written bytes.
"""
from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def release_blockers(root=ROOT):
    """Always fail closed: this repository has no implemented release selector."""
    reasons = ['Automated release selector is not implemented; historical format PASS is not submission clearance.']
    for relative in ['evidence/run_card.json', 'registry/lane.json', 'registry/cache_manifest.json']:
        try:
            value = json.loads((root / relative).read_text())
            if not isinstance(value, dict):
                raise ValueError('expected object')
        except (OSError, ValueError):
            reasons.append(f'Missing or malformed required evidence: {relative}')
            continue
        if relative.endswith('run_card.json'):
            reasons.extend(str(x) for x in value.get('blockers', []))
            if value.get('safe_to_submit') is not True:
                reasons.append('Current run card does not clear submission.')
        elif relative.endswith('lane.json') and (value.get('status') != 'assigned' or not value.get('method_paragraph')):
            reasons.append('No explicit single-method lane assignment.')
        elif relative.endswith('cache_manifest.json') and not value.get('cache_files'):
            reasons.append('Pinned transformed feature cache is unavailable.')
    return list(dict.fromkeys(reasons))


def page(title, body, reasons):
    items = ''.join(f'<li>{escape(r)}</li>' for r in reasons)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · GEMSDOE85</title>
<style>body{{margin:0;background:#101722;color:#e6edf3;font:17px/1.65 system-ui}}main{{max-width:960px;margin:auto;padding:32px 22px}}a{{color:#92c9ff}}nav{{display:flex;gap:24px;flex-wrap:wrap}}.status{{border:2px solid #e9ac60;background:#302619;padding:24px;border-radius:12px;margin:24px 0}}h1{{line-height:1.2}}code,pre{{overflow-wrap:anywhere;white-space:pre-wrap}}table{{border-collapse:collapse}}td,th{{border:1px solid #637083;padding:12px;text-align:left}}footer{{margin-top:40px;border-top:1px solid #637083;padding-top:16px}}</style></head><body><main>
<nav><a href="/docs/index.html">Status</a><a href="/docs/executive-summary.html">How to submit</a><a href="/docs/method.html">Research</a><a href="/docs/data.html">Sources</a></nav>
<h1>{escape(title)}</h1><section class="status"><h2>BLOCKED — DO NOT SUBMIT</h2>
<p>No new unique submission TIFF was generated in this review. Historical files are not approved for submission.
Format validity alone does not establish uniqueness, scientific improvement, or eligibility.</p><ul>{items}</ul></section>
{body}<footer>Review date: 2026-10-23. No weekly submission slot used. No human inspection is a release gate.
<a href="https://github.com/buffedlizard55-lab/GEMSDOE85">Repository and historical artifacts</a>.
AI assistance must be disclosed as required by the competition rules.</footer></main></body></html>'''


def build(root=ROOT):
    docs = root / 'docs'
    docs.mkdir(exist_ok=True)
    reasons = release_blockers(root)
    status = '''<h2>Executive summary</h2><p>The literal registry overlap gate is saturated by a positive continuous prior.
Every nonempty candidate in the allowed domain overlaps it above the permitted threshold. No policy exemption
has been applied. This is a negative protocol preflight, not a geological experiment.</p>
<p><a href="evidence/run_card.json">Download the JSON run card</a> ·
<a href="evidence/review_passes_20261023.json">Three-pass verification record</a></p>
<p>H33's owner-reported result is not receipt-verified. Sparse nonredundant dots can reduce false-positive mass
without reducing maximum distance-weighted coverage; this plausibly helps the metric but does not prove the
cause of its reported result or predict a higher score. Catalogue-based holdouts cannot establish live-board performance.</p>'''
    instructions = '''<h2>Exact submission workflow — unavailable until automated gates pass</h2>
<ol><li>Obtain an explicit method lane and the pinned template feature cache. Resolve the literal registry-support
policy conflict without silently changing the threshold.</li><li>Run feature-alone leakage canaries. Withhold whole fault segments with buffers; recompute catalogue features using visible faults only; mask visible faults pixel-exactly.</li>
<li>Beat a same-split incumbent using pooled HOLDOUT-DTI and report evaluator version, withheld positives and paired spatial uncertainty. Projections are not scores.</li>
<li>Pass registry checks before placement and on final dots. Use the pinned shared writer; reopen the output and verify single-band float32, reference CRS, shape, transform, finite in-footprint values and range [0,1].</li>
<li>The separate selector must authorize a weekly slot after checking the account's remaining quota. This selector is not implemented here.</li>
<li>Only then publish a uniquely named TIFF and a note of at most 140 characters. On the organizer submission page choose the TIFF (or ZIP containing only it), paste the note, and submit. Save the organizer receipt.</li></ol>
<p>There is currently no authorized file or submission name. Do not upload a historical, sample, or renamed file.
The earlier range-error message alone does not prove that outside-footprint NaNs caused rejection; unnormalized logits,
sentinels, infinities, or in-footprint NaNs must all be checked. Use a conservative zero-outside export, not silent clipping.</p>'''
    research = '''<h2>Research and evidence boundaries</h2><p>The task is fault discovery, not direct proof of geothermal vents, reservoir productivity, or usable heat.</p>
<p>The ranked hypothesis review, layers, physical signatures, mimics and validation plan are in the
<a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/arena/e35c6a93-gemsdoe85/research/session-20261023-review.md">session research record</a>.
No hypothesis was selected as a lane or evaluated this session. No current HOLDOUT-DTI or organizer-confirmed score is reported.</p>'''
    sources = '''<h2>Official sources for review</h2><p>Non-GitHub official hosts cannot be independently re-fetched from this sandbox's outbound allowlist.
These are source links, not claims of fresh verification. Owner mirrors prove pinned-byte consistency, not organizer authentication.</p><ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Organizer problem description and metric</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Organizer data</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">Organizer submissions and account quota</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF</a></li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b">Organizer reference solution (commit verified this session)</a></li>
<li><a href="https://doi.org/10.5066/P93LGLVQ">USGS GeoDAWN</a></li>
<li><a href="https://gdr.openei.org/submissions/1391">INGENIOUS GDR release</a></li></ul>'''
    pages = {'index.html': ('Submission status', status), 'executive-summary.html': ('How to submit', instructions),
             'method.html': ('Research and validation', research), 'data.html': ('Data and sources', sources)}
    # Old public URLs must not retain contradictory release claims or download links.
    for path in docs.rglob('*.html'):
        relative = path.relative_to(docs).as_posix()
        if relative not in pages:
            pages[relative] = ('Historical page — not submission cleared', '<p>This historical public URL is superseded. Use the navigation above for current evidence. Prior research remains in Git history and repository research files.</p>')
    for relative, (title, body) in pages.items():
        # Relative links work for both root and /docs GitHub Pages configurations.
        prefix = '../' * (len(Path(relative).parts) - 1)
        text = page(title, body, reasons).replace('href="/docs/', f'href="{prefix}')
        (docs / relative).write_text(text)
    for directory in ['evidence', 'registry']:
        target = docs / directory
        target.mkdir(exist_ok=True)
        names = {path.name for path in target.glob('*.json')}
        if directory == 'evidence':
            names.update(['run_card.json', 'review_passes_20261023.json'])
        for name in sorted(names):
            path = root / directory / name
            if path.is_file():
                shutil.copyfile(path, target / name)
    (docs / '.nojekyll').write_text('')
    (root / 'index.html').write_text('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0; url=docs/index.html"><title>GEMSDOE85 — blocked</title></head><body><h1>BLOCKED — DO NOT SUBMIT</h1><p>No new unique TIFF is approved. <a href="docs/index.html">Open current status and executive summary</a>.</p></body></html>''')
    return 0


main = build
if __name__ == '__main__':
    raise SystemExit(build())
