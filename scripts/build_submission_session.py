#!/usr/bin/env python3
"""Retired historical CTXFUS exporter — never writes or relabels a prior TIFF.

The previous implementation used a private writer and an unauthorized
partial-registry/chance-corrected uniqueness rule. Its original scientific
recipe remains in Git history at 046761a22c3787730418557ac1c94c0a0f874101.
Future authorized exports must use the pinned shared submission_writer.py,
not re-enable this obsolete path.
"""
from pathlib import Path
from preflight import review

ROOT = Path(__file__).resolve().parents[1]


def main():
    decision = review(ROOT)
    print('BLOCKED — DO NOT SUBMIT. Historical session exporter is retired; no TIFF written.')
    for reason in decision['blockers']:
        print('- ' + reason)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
