# H85 evidence downloads

**Status: DO NOT SUBMIT.** The files in this directory are retained for reproducibility and
format review. They are not an upload recommendation.

- `gems85-h85-scalescarp-persistence-20261022T220819Z-zeros.tif` is the formal 60,000-dot
  candidate. Its GeoTIFF validator passed, but its registry uniqueness audit failed with a
  maximum final three-pixel overlap of `0.9939166667`.
- `gems85-h85-scalescarp-persistence-20261022T220819Z-unique-selector-DO-NOT-SUBMIT-zeros.tif`
  is a separate selector-only negative control. Its validator passed, but its final overlap
  was `0.9557564414`; it is explicitly not a repair or a submission candidate.
- The adjacent ZIPs each contain exactly one GeoTIFF and are retained only to test the expected
  archive shape.

The machine receipts are next to the files and the full run cards are in `../run-card.json`,
`../selector-run-card.json`, and the repository `evidence/` directory. No file here has an
`ORGANIZER-CONFIRMED` score.
