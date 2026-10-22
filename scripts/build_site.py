#!/usr/bin/env python3
"""Build a static, evidence-linked blocked-status site. Never fabricate a TIFF link."""
from __future__ import annotations
import html
import json
from pathlib import Path
import shutil
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
E = html.escape


def layout(title, body, active='index.html'):
    links = [('index.html', 'Overview'), ('executive-summary.html', 'How to submit'),
             ('hypotheses.html', 'Research'), ('why-h33.html', 'H33 analysis'),
             ('sources.html', 'Sources'), ('review.html', 'Review')]
    nav = ''.join(f'<a href="{url}"'+(' aria-current="page"' if url == active else '')+f'>{label}</a>' for url, label in links)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evidence-first GEMS fault-discovery review. No verified submission is available; see automated preflight and scientific blockers.">
<title>{E(title)} · GEMSDOE85</title><link rel="stylesheet" href="style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header><div class="brand"><a href="index.html">GEMS<span>DOE85</span></a><small>FAULT DISCOVERY / RESEARCH LOG</small></div><nav aria-label="Main navigation">{nav}</nav></header>
<main id="main">{body}</main><footer><strong>Evidence before emission.</strong><span>Maximize P(Win) · Own the Outcome</span><p>Fault predictions are not proof of a geothermal resource. Local validation is not organizer acceptance.</p><a href="https://github.com/buffedlizard55-lab/GEMSDOE85">Repository &amp; reproducibility</a> · <a href="evidence/run_card.json">Machine-readable run card</a></footer></body></html>'''


def md_page(name, file, title):
    text = (ROOT / file).read_text()
    # Research markdown uses repo-relative evidence/registry links. Published copies live in docs.
    text = text.replace('../evidence/', 'evidence/').replace('../registry/', 'registry/')
    for old, new in [('why-h33.md', 'why-h33.html'), ('hypotheses.md', 'hypotheses.html')]:
        text = text.replace(f']({old})', f']({new})')
    content = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    return layout(title, '<article class="prose">' + content + '</article>', name)


def build():
    DOCS.mkdir(exist_ok=True)
    card = json.loads((ROOT / 'evidence/run_card.json').read_text())
    # This builder implements only the current blocked research portal, not a release selector.
    if card.get('safe_to_submit') is not False or card.get('safe_to_download') is not False or card.get('raster_sha256') is not None:
        raise ValueError('This blocked-review builder cannot publish or approve candidate artifacts')
    if card.get('verdict') != 'negative' or not card.get('blockers'):
        raise ValueError('Negative verdict and explicit blockers required')
    for folder, files in {
        'evidence': ['run_card.json', 'saturation_certificate.json', 'h33_learning_audit.json', 'input_audit.json', 'data_restore.json', 'review_passes.json'],
        'registry': ['sources.json', 'public_inventory.json', 'template_pin.json', 'data_manifest.json', 'learning_manifest.json', 'lane.json', 'cache_manifest.json'],
    }.items():
        (DOCS / folder).mkdir(exist_ok=True)
        for file in files:
            shutil.copyfile(ROOT / folder / file, DOCS / folder / file)
    blockers = ''.join('<li>' + E(s) + '</li>' for s in card['blockers'])
    inventory = json.loads((ROOT / 'registry/public_inventory.json').read_text())
    count = len(inventory['repositories'])
    possible = sum(r['role'] == 'possible-prior-prediction' for row in inventory['repositories'] for r in row['rasters'])
    body = f'''<section class="hero"><p class="eyebrow">GEOLOGIC ENHANCED MAPPING SYSTEM · DOE GEMS PRIZE</p><h1>Better fault evidence.<br>Not another renamed raster.</h1><p class="lead">An auditable research system for finding missing faults in the GeoDAWN region. We publish what the evidence supports—and stop when the gates fail.</p></section>
<section class="submission" aria-labelledby="submission-status"><div><span class="badge">BLOCKED · NEGATIVE PREFLIGHT</span><h2 id="submission-status">No verified submission TIFF is available.</h2><p><strong>Do not download an old submission or the sample and submit it as this run.</strong> No new candidate has passed scientific, uniqueness or slot-selection gates. No weekly slot was used.</p><p>This is a prerequisite/policy failure, not a failed geological hypothesis. No model experiment was run.</p><div class="actions"><a class="button" href="executive-summary.html">Submission status &amp; next steps</a><a class="button secondary" href="evidence/run_card.json" download>Download negative run card</a></div></div><div class="artifact"><span>SUBMISSION ARTIFACT</span><strong>Not generated</strong><dl><dt>Safe to submit</dt><dd>NO</dd><dt>Unique-cleared</dt><dd>NO</dd><dt>Candidate HOLDOUT-DTI</dt><dd>Not measured</dd><dt>Candidate SHA-256</dt><dd>Not available</dd></dl></div></section>
<p class="timestamp">Automated preflight: {E(card['reviewed_utc'])}. Source-page research: 2026-10-22. This is a dated snapshot, not a live organizer feed.</p>
<section><p class="eyebrow">THE DECISIVE FINDING</p><h2>The literal overlap gate is saturated.</h2><div class="grid"><div class="panel"><h3>A prior covers the entire footprint</h3><p>The shared template verified a registry surface with positive support throughout the study area. Every nonempty candidate would be within its three-pixel halo, so it cannot pass the literal overlap rule.</p><p><a href="evidence/saturation_certificate.json">Read the measured certificate →</a></p></div><div class="panel"><h3>No silent exemptions</h3><p>We did not exclude dense priors, alter the dot definition, add noise, or copy H33. The missing explicit lane and transformed feature cache also block experiments.</p><p><a href="review.html">Review all irregularities →</a></p></div></div></section>
<section><h2>What is verified today</h2><div class="grid thirds"><div class="panel"><span class="tag">INPUT INTEGRITY</span><h3>Core mirrors restored</h3><p>Features, labels, mapped faults and the sample grid were hash-verified. Owner mirrors are not authenticated organizer downloads.</p><a href="evidence/input_audit.json">Input audit</a></div><div class="panel"><span class="tag">RESEARCH, NOT A SCORE</span><h3>Four falsifiable ideas</h3><p>Ranked by qualitative promise and cost, each with named layers, physical signatures and a non-fault mimic. None is assigned or tested.</p><a href="hypotheses.html">Research shortlist</a></div><div class="panel"><span class="tag">SHARED TOOLS</span><h3>No private metric fork</h3><p>The evaluator, literal uniqueness code and fail-closed TIFF writer are pinned and unmodified. Contract tests are not geological validation.</p><a href="registry/template_pin.json">Source pins</a> · <a href="evidence/review_passes.json">Three-pass verification</a></div></div></section>
<section><h2>Why study H33?</h2><p>Its sparse-dot structure and near-catalogue pruning can reduce redundant prediction mass under a maximum-cover metric. That is a plausible mechanism, not proof of the cause of its owner-reported result or a promise of a higher score.</p><a href="why-h33.html">Read the mathematical and byte-level analysis →</a></section>
<section><h2>Remaining gates</h2><ul class="blockers">{blockers}</ul></section>
<section class="panel"><h2>Registry scope, stated honestly</h2><p>Public Git-tree metadata for {count} repository names includes {possible:,} possible-prior TIFF paths, including archived copies. These are inventory counts, not distinct submissions or performance scores. The raster bytes were not all compared.</p><p>Metadata snapshot: {E(inventory['checked_utc'])}. Scheduled/manual refresh uploads an Actions artifact; it cannot silently promote a candidate or update this verdict.</p><a href="registry/public_inventory.json">Download metadata inventory</a> · <a href="sources.html">Claim-level official sources</a></section>'''
    (DOCS / 'index.html').write_text(layout('Submission status', body))
    summary = '''<article class="prose"><p class="eyebrow">EXECUTIVE SUMMARY</p><h1>How to make a competition submission</h1><div class="notice"><h2>Current decision: do not submit.</h2><p>No new submission TIFF, candidate name, or candidate SHA-256 exists. No scientific improvement or uniqueness clearance is claimed. <a href="evidence/run_card.json">Download the negative run card</a>.</p></div>
<h2>Why there is no download button for a TIFF</h2><p>The literal registry overlap policy excludes every nonempty candidate because a prior has positive support across the whole footprint. An explicit method lane and the exact transformed cache are also missing. Publishing an old or arbitrary raster would not solve these failures.</p><p>This project automates its current checks; it does not require a human to visually inspect a TIFF. Resolving a missing assignment or contradictory policy is not an image-inspection task. The separate organizer expert review is part of the official competition structure and cannot be replaced by this project.</p>
<h2>Required path before a file is offered</h2><ol><li>Resolve the literal overlap policy and supply the explicit parallel-run lane; restore the exact cached feature stack with provenance.</li><li>Implement only that lane. Withhold whole fault components with a buffer. Compute catalogue features from fold-visible faults only; mask non-withheld mapped faults exactly.</li><li>Test every feature alone as a leakage canary. Stop for suspicious AUC until investigated. Evaluate candidate and current incumbent on the same spatial holdout with the shared pooled DTI evaluator and paired confidence intervals.</li><li>Beat the comparable incumbent before asking a separate selector to consider a slot. A holdout gain is not a guaranteed public/private gain.</li><li>Check rank correlation on the surface before placement and literal dot-overlap/correlation again after placement against the complete accessible registry. Stop and log duplicates.</li><li>Package via the unmodified shared writer. Reopen the exact TIFF bytes, verify the grid/range/footprint and one-TIFF ZIP, and publish the SHA-256 plus a unique name and a note of at most 140 characters.</li><li>Only the separate selector may approve a weekly slot after checking the account-specific quota on the authenticated organizer submission page.</li></ol>
<h2>File format checklist</h2><p>The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format">official format specification</a> calls for a single float32 layer with confidence values in [0,1], matching the reference CRS, shape, bounds and geotransform. The mirror reference is EPSG:32611 at 100 m resolution, with height 3730 and width 3292. These are format constants, not scores.</p><p>The template uses the conservative all-finite, no-nodata, zero-outside policy. The public spec permits null/NaN outside bounds; we cannot infer the cause of the previous range error from its wording alone. Reject out-of-range model output rather than silently clipping it. Local format PASS is not organizer acceptance.</p><pre><code>.venv/bin/python scripts/validate_submission.py path/to/candidate.tif</code></pre>
<h2>When an approved file eventually exists</h2><p>These are organizer upload instructions for a future approved artifact, not permission to submit today. No automatic upload or selector is implemented.</p><ol><li>Download only the current approved candidate TIFF (or its ZIP containing exactly one TIFF), along with the matching receipt. Confirm the recorded hash automatically in the release pipeline.</li><li>Sign in to DrivenData and open the competition's <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">submission area</a>. Check the remaining quota and current rules. Do not use a slot to diagnose formatting.</li><li>In “File to submit,” choose that exact TIFF or single-TIFF ZIP. Use the release's unique submission name and its supplied short note. No pasteable candidate name/note is issued by this blocked run.</li><li>Submit only after separate slot approval. Save the resulting submission-page receipt, artifact hash, organizer validation outcome and returned score. Only that receipt supports ORGANIZER-CONFIRMED performance.</li></ol>
<p><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules §3.2</a> states a weekly cap of three, subject to competition-site limits. This session could not access the account's remaining quota and spent no slot. Generative-AI development assistance must be disclosed in the required narrative; this project used an AI coding agent.</p>
<h2>Current limitations</h2><p>This static site is a status/research portal, not a browser training service. No lane-specific model, feature-canary runner, full registry comparison, paired incumbent experiment, selector or upload automation is implemented. Core mirror bytes were restored, but their official origin is not independently authenticated. A useful competition submission remains blocked, not “inspection pending.”</p><p><a href="review.html">Full dependency-ordered next steps</a> · <a href="sources.html">Sources and access receipts</a></p></article>'''
    (DOCS / 'executive-summary.html').write_text(layout('How to submit', summary, 'executive-summary.html'))
    for name, file, title in [('hypotheses.html', 'research/hypotheses.md', 'Research shortlist'),
                              ('why-h33.html', 'research/why-h33.md', 'H33 analysis'),
                              ('review.html', 'research/review.md', 'Repository review')]:
        (DOCS / name).write_text(md_page(name, file, title))
    sources = json.loads((ROOT / 'registry/sources.json').read_text())
    rows = ''.join(f'<tr><th scope="row"><a href="{E(s["url"], quote=True)}">{E(s["id"])}</a><br><small>{E(s["class"])}</small></th><td>{E(s["status"])}</td><td>{E(s["supports"])}</td><td>{E(s["limits"])}</td></tr>' for s in sources['sources'])
    source_body = '<section><p class="eyebrow">CLAIM-LEVEL EVIDENCE</p><h1>Sources, not assumptions.</h1><p>Checked 2026-10-22. Links are provided for audit, not as a substitute for automated validation. Retrieval notes are not signed receipts. Owner reports, input measurements and organizer scores are kept separate.</p><div class="table-scroll"><table><thead><tr><th>Source / authority</th><th>Access checked</th><th>What it supports</th><th>What it does not prove</th></tr></thead><tbody>' + rows + '</tbody></table></div><p><a href="registry/sources.json" download>Download the source register</a></p><h2>Performance evidence standard</h2><p>No candidate performance measurement is reported. Future HOLDOUT-DTI results require evaluator version, withheld positives and conditional 95% CI. ORGANIZER-CONFIRMED requires a submission-page receipt. Historical owner reports and public leaderboard observations cannot honestly be forced into those classes.</p><h2>Not a live feed</h2><p>The public leaderboard was retrieved during this review, but there is no authenticated organizer feed. Scheduled inventory refreshes produce GitHub Actions artifacts; they do not automatically change this site\'s verdict or certify new artifacts.</p></section>'
    (DOCS / 'sources.html').write_text(layout('Verified sources', source_body, 'sources.html'))
    (ROOT / 'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; url=docs/index.html"><title>GEMSDOE85 · Submission status</title></head><body><h1>GEMSDOE85</h1><p>No verified submission TIFF is available. <a href="docs/index.html">Open the status and research site</a>.</p></body></html>\n')
    print('Built blocked-status site; no TIFF or candidate download link generated.')


if __name__ == '__main__':
    build()
