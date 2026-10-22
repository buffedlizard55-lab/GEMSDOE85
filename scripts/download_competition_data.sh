#!/usr/bin/env bash
# Download the public mirrors named in the competition data workflow.
# This script does not bypass DrivenData authentication and never accepts or
# stores credentials. Run it only on a machine whose policy permits the
# official/mirror hosts; the Arena sandbox intentionally cannot reach them.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/data/raw"
mkdir -p "$OUT"
fetch() { local url="$1" dest="$2"; echo "fetching $dest"; curl --fail --location --retry 3 --output "$OUT/$dest.tmp" "$url"; mv "$OUT/$dest.tmp" "$OUT/$dest"; }

# Official enrollment/data tab (manual account download route):
# https://www.drivendata.org/competitions/306/competition-doe-gems/data/
# Owner-provided mirror URLs listed in the project brief:
fetch 'https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&dl=1' training_features.tif
fetch 'https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&dl=1' existing_faults.tif
cp "$OUT/existing_faults.tif" "$OUT/labels.tif"
fetch 'https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&dl=1' sample_submission.tif

# Hash gates. A mismatch is an abort, never a warning.
sha256sum --check <<'EOF'
4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5  data/raw/training_features.tif
7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093  data/raw/labels.tif
7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093  data/raw/existing_faults.tif
2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc  data/raw/sample_submission.tif
EOF
python "$ROOT/scripts/prepare_data.py" --features "$OUT/training_features.tif"
