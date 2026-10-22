#!/usr/bin/env python3
"""Canonical fail-closed publication. Historical format PASS cannot authorize a slot."""
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    docs = root / 'docs'
    card = json.loads((root / 'evidence/run_card.json').read_text())
    if card.get('verdict') != 'negative' or card.get('safe_to_submit') is not False:
        raise ValueError('No authorized promotion implementation: refusing publication')
    if list(docs.rglob('*.tif')) or list(docs.rglob('*.zip')):
        raise ValueError('Unapproved public binary; quarantine before publishing')
    for folder in ['evidence', 'registry']:
        (docs / folder).mkdir(exist_ok=True)
        # Publish only already-public records; no credentials or input arrays.
        for old in (docs / folder).glob('*.json'):
            if (root / folder / old.name).exists():
                shutil.copyfile(root / folder / old.name, old)
    shutil.copyfile(root / 'evidence/run_card.json', docs / 'evidence/run_card.json')
    nav = ' · '.join(f'<a href="{name}">{label}</a>' for name, label in [
        ('index.html','Status'), ('executive-summary.html','How to submit'),
        ('hypotheses.html','Research'), ('why-h33.html','H33 analysis'), ('sources.html','Sources')])
    common = '''<section class="hero"><p class="badge">AUTOMATED DECISION · NEGATIVE</p>
<h1>Current decision: do not submit</h1>
<p>No verified submission TIFF is available. Historical TIFFs are quarantined outside the Pages directory.
Their format validity does not establish uniqueness, holdout improvement, or permission to use a slot.</p>
<p><a href="evidence/run_card.json">Download the machine-readable audit (JSON)</a></p></section>'''
    bodies = {
        'executive-summary.html': '''<h2>How a future approved submission will work</h2>
<ol><li>Run the shared evaluator on whole-segment buffered hide-and-recover splits. Build every catalogue feature from visible faults only; mask visible faults pixel-exactly.</li>
<li>Run each feature's leakage canary. Investigate AUC above the protocol ceiling before trusting results.</li>
<li>Beat the current incumbent on the same pooled HOLDOUT-DTI instrument; report its version, withheld positives, conditional confidence interval, and paired uncertainty.</li>
<li>Pass literal registry correlation and overlap checks on the surface before placement and again on final dots. No dense-prior exemption or chance-correction override is authorized.</li>
<li>Write through the pinned shared writer. Independently reopen the written file and verify one float32 band, finite footprint values in [0,1], and matching CRS, shape and transform. Conservative export uses zeros outside the footprint.</li>
<li>A separate selector must verify the account's live weekly cap and authorize a slot. Only then may a one-click TIFF download appear here.</li>
<li>On the organizer's New submission form, choose that exact TIFF (or a ZIP containing only it), paste its unique short note, and save the submission receipt. Acceptance and score are not inferred from local checks.</li></ol>
<p>The previous range-error message alone does not identify its cause. Our audit separately checks written pixel ranges; a JSON metadata claim is not a substitute.</p>''',
        'why-h33.html': '''<h2>What the reported H33 result can tell us</h2>
<p>The historical H33 score in the user brief is OWNER-REPORTED, not ORGANIZER-CONFIRMED: no submission-page receipt was supplied. Competing leaderboard claims in the brief are not current verified observations.</p>
<p>A sparse off-catalogue dot field can reduce redundant prediction mass under a maximum-coverage, distance-weighted Tversky objective. Pruning near catalogue traces is a plausible efficiency mechanism, not proof that deleted dots were false positives.</p>
<p>Hidden truth, captured credit, and fault length cannot be uniquely reconstructed from reported scores and dot counts. Earlier README back-solves assumed unverified invariances. Neither an exact causal explanation nor a better leaderboard score follows from those equations.</p>
<p>To establish improvement requires matched ablations, the same fold-visible masking, a valid incumbent, and eventually an organizer receipt. No new candidate has passed those gates in this session.</p>''',
        'hypotheses.html': '''<h2>Research-only shortlist; no method lane selected</h2>
<p>Ranked by qualitative scientific potential versus engineering cost, not projected DTI. These are previously recorded proposals, not newly tested discoveries. Novelty against merged implementations and sibling lanes remains unverified.</p>
<table><tr><th>Priority / cost</th><th>Layers and physical signature</th><th>Missing-fault rationale / difference / mimic</th></tr>
<tr><td>First / medium</td><td>Basement-depth proxy, surface conductivity, gravity: signed paired-flank offset and flexure</td><td>May detect buried steps without scarps; profile ordering rather than GEO-Pb magnitude consensus. Sedimentary facies and erosional basement relief can mimic it. Resolve depth-layer provenance first.</td></tr>
<tr><td>Second / medium</td><td>Gravity anomaly and derivatives: persistent opposite-polarity curvature lobes</td><td>Concealed density step; signed profile rather than gradient worms. Unfaulted lithological contacts can mimic it.</td></tr>
<tr><td>Third / medium-high</td><td>Magnetic field and derivatives, basement-depth proxy, terrain slope: displaced coherent edges under low relief</td><td>Possible covered continuation; cross-scale displacement rather than edge strength. Intrusive contacts and remanence are confounders.</td></tr>
<tr><td>Fourth / high</td><td>Terrain and slope: matched cross-drainage residual facet discontinuities</td><td>Possible weak unmapped scarps; matched residuals rather than raw ridge crests. Lake terraces, bedding and incision can mimic it.</td></tr></table>
<p>These proposals use supplied layers only, but the required pinned transformed cache is unavailable. No new external source is represented as obtainable or as already validated. The overlap-stop condition prevents testing a promotable candidate under the unchanged protocol.</p>''',
        'sources.html': '''<h2>Source register and verification limits</h2>
<p>External official websites below are provided for review, not claimed freshly retrieved in this session. Network access permits GitHub and package registries, not DrivenData, USGS, GDR or the rules PDF. Historical source-retrieval notes are inherited evidence, not a fresh verification.</p>
<ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Organizer task, metric and format</a></li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Live leaderboard — current position not verified here</a></li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference implementation — GitHub repository availability checked</a></li>
<li><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules PDF — not freshly fetched</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a></li>
<li><a href="https://gdr.openei.org/submissions/1391">INGENIOUS GDR dataset</a></li></ul>
<p>Fault detection is not proof of geothermal vents, productive permeability, temperature, or a commercial reservoir. These require independent evidence.</p>'''
    }
    sat = card['registry'].get('saturation_certificate')
    status = '<h2>Why release is blocked</h2><ul>' + ''.join('<li>'+html.escape(x)+'</li>' for x in card['blockers']) + '</ul>'
    status += '<p>REGISTRY-MEASUREMENT: ' + ('the pinned witness was re-fetched, SHA-256 verified, and remeasured with the unmodified shared saturation function; every allowed cell is covered by its literal overlap halo.' if sat and sat['universal_overlap_blocker'] else 'witness not locally verified; no uniqueness clearance.') + '</p>'
    status += '<p>No geological experiment or submission slot used this session. Historical holdout runs use different evaluators and cannot be ranked against each other.</p>'
    targets = set(docs.glob('*.html')) | {docs / name for name in bodies}
    targets |= set((docs / 'duplex-lane').glob('*.html'))
    for target in sorted(targets):
        # Nested legacy URLs remain usable, but never retain their old submit banners.
        prefix = '../' if target.parent != docs else ''
        body = bodies.get(target.name, status)
        content = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GEMSDOE85 — release audit</title><style>
body{{margin:0;background:#0b1320;color:#e3eaf3;font:17px/1.65 system-ui}}main{{max-width:1050px;margin:auto;padding:32px 24px}}a{{color:#86c7ff}}nav{{margin-bottom:28px}}.hero{{background:#271d23;border:1px solid #e9908a;padding:26px;border-radius:14px}}h1{{line-height:1.2}}.badge{{font-size:13px;letter-spacing:.1em;color:#ffb1a5}}table{{border-collapse:collapse}}td,th{{padding:12px;border:1px solid #40516a;text-align:left;vertical-align:top}}code{{overflow-wrap:anywhere}}
</style></head><body><main><nav>{nav}</nav>{common}{body}<footer><p>Audit date: 2026-10-22 · No organizer score claimed · AI-assisted research</p></footer></main></body></html>'''
        if prefix:
            import re
            content = re.sub(r'href="(?!https?://)([^"]+)"', lambda m: 'href="../' + m[1] + '"', content)
            content = content.replace('<base href="../../">', '')
        target.write_text(content)
    (root / 'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=docs/index.html"><title>GEMSDOE85 — blocked</title></head><body><h1>Current decision: do not submit</h1><p><a href="docs/index.html">Open the automated release audit</a></p></body></html>')


def main():
    build()
    print('Published negative release audit; no TIFF download authorized.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
