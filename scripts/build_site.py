#!/usr/bin/env python3
"""Deterministic, fail-closed status publisher. Never selects a competition slot.

Historical builders and exports are retained for research only. This publisher supports
only the current blocked decision; a future promotion must implement the complete gate.
"""
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    docs = root / 'docs'
    card = json.loads((root / 'evidence/run_card.json').read_text())
    if card.get('verdict') != 'negative' or card.get('safe_to_submit') is not False:
        raise ValueError('No implemented promotion selector: refusing to publish an approval')
    if card.get('safe_to_download') is not False:
        raise ValueError('Blocked run must not advertise a candidate download')
    if any(p.suffix.lower() in {'.tif', '.tiff', '.zip'} for p in docs.rglob('*')):
        raise ValueError('Quarantine unapproved binary exports outside docs before building')
    for directory in ['evidence', 'registry']:
        (docs / directory).mkdir(exist_ok=True, parents=True)
        for p in (root / directory).glob('*.json'):
            # Historical results remain in Git, not mixed with the current public decision.
            if p.name in {'run_card.json', 'saturation_certificate.json', 'lane.json',
                          'cache_manifest.json', 'sources.json', 'template_pin.json'}:
                shutil.copyfile(p, docs / directory / p.name)
    nav = '<nav><a href="{prefix}index.html">Status</a> · <a href="{prefix}executive-summary.html">Submission instructions</a> · <a href="{prefix}hypotheses.html">Research</a></nav>'
    banner = '<section class="blocked"><h1>Current decision: do not submit</h1><p><strong>No verified submission TIFF is available.</strong> Historical TIFFs are quarantined, not approved submissions. Format PASS alone does not establish uniqueness or predictive skill.</p></section>'
    blockers = '<ul>' + ''.join('<li>' + html.escape(x) + '</li>' for x in card['blockers']) + '</ul>'
    body = {
        'index.html': '<h2>Automated preflight</h2>' + blockers + '<p><a href="evidence/run_card.json">Current JSON run card</a> · <a href="evidence/saturation_certificate.json">Literal overlap obstruction</a></p><h2>Why no download?</h2><p>The historical GEO-Pb run card reports overlap 0.991433, above the required 0.70 threshold. Its chance-corrected exemption is not authorized. Existing artifact bytes are preserved in the repository under submissions/quarantine for education only.</p><p>No new experiment or competition upload was run in this safety review. No improved leaderboard score is claimed.</p>',
        'executive-summary.html': '<h2>How submission will work after all gates pass</h2><ol><li>Use the assigned single-method lane and integrity-pinned shared feature cache, evaluator and writer.</li><li>Run feature-alone leakage canaries; AUC above 0.90 blocks trust pending investigation.</li><li>Withhold whole fault segments with buffers; derive catalogue features only from visible faults. Compare candidate and incumbent on identical splits using pooled HOLDOUT-DTI and paired spatial uncertainty.</li><li>Stop if pre-placement surface or final dots exceed the literal registry correlation/overlap thresholds. No dense-prior exemption is authorized.</li><li>Use the shared writer. Reopen the exact exported bytes and validate single band, float32, finite footprint, range [0,1], and matching sample CRS, shape and transform. Publish a SHA-256 and unique name with a note of at most 140 characters.</li><li>A separate selector may approve a weekly slot only after the incumbent is beaten and account quota/rules are verified. The site will then show an approved download; none exists now.</li><li>On DrivenData choose New submission, select the approved .tif (or ZIP containing only that TIFF), paste its note, and submit. Preserve the organizer receipt. Never upload a sample, prior, or quarantined artifact.</li></ol><p>The earlier range error does not prove NaN was its cause. An all-finite [0,1] export is a conservative safeguard, not organizer acceptance.</p>',
        'hypotheses.html': '<h2>Research proposals, not lane assignments</h2><p>Four ranked, untested hypotheses are retained in <a href="https://github.com/buffedlizard55-lab/GEMSDOE85/blob/main/research/hypotheses.md">the research register</a>: paired basin-interface flexure; gravity curvature polarity reversal; depth-conditioned magnetic edge displacement; cross-drainage residual facets. Each names layers, transforms, catalogue-missing rationale and mimics. No new external data is assumed. Novelty versus the merged implementations is unverified; do not start a different lane.</p><h2>H33 interpretation</h2><p>Sparse off-catalogue dots can trade recall against false-positive mass under maximum-distance coverage. Pruning redundant mass can help, but no hidden labels or organizer receipt here prove the cause of the owner-reported 0.2778 result. It cannot justify a forecast above that result.</p><h2>Official references</h2><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Organizer problem and format (not freshly reachable from this sandbox)</a></li><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference implementation (GitHub README rechecked in this review)</a></li><li><a href="https://gdr.openei.org/submissions/1391">INGENIOUS database (official link, not freshly verified)</a></li></ul><p>The competition predicts fault traces, not demonstrated geothermal vents or productive reservoirs. Owner mirrors are hash-pinned but not organizer-authenticated. Reported leaderboard values conflict and no current team submission receipt was obtained.</p>'
    }
    # Replace every old entry point, including archived lane portals, with a clear blocked page.
    pages = {p.relative_to(docs).as_posix() for p in docs.rglob('*.html')} | set(body)
    for name in sorted(pages):
        path = docs / name
        prefix = '../' * (len(Path(name).parts) - 1)
        content = body.get(name, '<p>This historical lane portal is superseded. Return to the current status; its exports are not approved.</p>')
        path.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GEMSDOE85 — submission gate</title><style>body{max-width:960px;margin:40px auto;padding:0 22px;font:17px/1.65 system-ui;color:#172535;background:#f5f7fa}a{color:#1259a7}.blocked{background:#fff1da;border-left:6px solid #ae4e00;padding:20px;margin:24px 0}li{margin:10px 0}nav{padding:12px 0}h1{line-height:1.2}</style>' + nav.format(prefix=prefix) + banner + content + '<footer>GEMSDOE85 · automated fail-closed research status · 2026-10-22</footer></html>')
    (root / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0; url=docs/index.html"><title>GEMSDOE85 — blocked submission</title><h1>Current decision: do not submit</h1><p>No verified submission TIFF is available. <a href="docs/index.html">Open status and research</a>.</p></html>')
    (docs / '.nojekyll').touch()
    return card


def main():
    build()
    print('Published deterministic BLOCKED status; no candidate download or slot approval.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
