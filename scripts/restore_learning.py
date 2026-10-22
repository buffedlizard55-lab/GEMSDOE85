#!/usr/bin/env python3
"""Fetch prior predictions for education and the literal-gate witness; never publish."""
import json
from restore_data import ROOT, restore


def main():
    manifest = json.loads((ROOT / 'registry/learning_manifest.json').read_text())
    rows = [restore(entry, ROOT / 'data/raw/learning') for entry in manifest['files']]
    (ROOT / 'evidence/learning_restore.json').write_text(json.dumps(dict(
        policy=manifest['policy'], files=rows), indent=2) + '\n')
    print('Learning artifacts restored privately. Not new submissions.')


if __name__ == '__main__':
    main()
