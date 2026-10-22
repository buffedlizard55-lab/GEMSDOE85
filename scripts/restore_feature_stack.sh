#!/usr/bin/env bash
# Restore the 19-band feature stack without putting a 419 MB blob in this repo.
# Only GitHub is used; this mirrors the owner-supplied, hash-pinned bridge and
# is not an organizer authentication claim.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/data"
CACHE="$ROOT/.cache/gemsdoe-feature-bridge"
UPSTREAM="https://github.com/buffedlizard55-lab/GEMSDOE.git"
COMBINED_SHA="4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
# The c0c06... ref is the pinned bridge in the prior repository's manifest.
REF="c0c06ac82178f26b94fce3397036ef8f12a2f3a0"
PARTS=(
  "0a330f8951af6c921029e25c84a579319d2db554d62d30d894d6ddc97f98cff7"
  "3c98037b2c997e3bbfcdfc2d9a982e8b820a77410dd7404b05cdb80594922c50"
  "c375c4dbc40c59bbaece572b5e348700b75935f9a30c879c82b6417e0836f31c"
  "b164159e6d0cb2595bc9f63a948af2646b124114a9c5921880c7516092137320"
  "fa0a6f9c936fac1d6f20ca37f5929b2d60bf7a80f3d477dcab886f941aee2696"
)
mkdir -p "$CACHE" "$DATA"
if [[ ! -d "$CACHE/.git" ]]; then
  git clone --quiet --depth 1 "$UPSTREAM" "$CACHE"
fi
# The bridge is public in the upstream repository. Prefer the pinned ref when
# the shallow clone can fetch it; otherwise the current bridge still has to
# pass every part and whole-file hash gate below.
if ! git -C "$CACHE" cat-file -e "$REF^{commit}" 2>/dev/null; then
  git -C "$CACHE" fetch --quiet --depth 1 origin "$REF" 2>/dev/null || true
fi
PART_DIR="$CACHE/data/bridge"
for i in 0 1 2 3 4; do
  file="$PART_DIR/gems-geodawn-numerical-features.tif.part-00$i"
  test -f "$file" || { echo "missing feature-stack part: $file" >&2; exit 2; }
  actual="$(sha256sum "$file" | awk '{print $1}')"
  [[ "$actual" == "${PARTS[$i]}" ]] || { echo "part $i hash mismatch: $actual" >&2; exit 3; }
done
cat "$PART_DIR"/gems-geodawn-numerical-features.tif.part-000 \
    "$PART_DIR"/gems-geodawn-numerical-features.tif.part-001 \
    "$PART_DIR"/gems-geodawn-numerical-features.tif.part-002 \
    "$PART_DIR"/gems-geodawn-numerical-features.tif.part-003 \
    "$PART_DIR"/gems-geodawn-numerical-features.tif.part-004 > "$DATA/training_features.tif.tmp"
actual="$(sha256sum "$DATA/training_features.tif.tmp" | awk '{print $1}')"
[[ "$actual" == "$COMBINED_SHA" ]] || { echo "combined hash mismatch: $actual" >&2; rm -f "$DATA/training_features.tif.tmp"; exit 4; }
mv "$DATA/training_features.tif.tmp" "$DATA/training_features.tif"
echo "restored and verified $DATA/training_features.tif ($COMBINED_SHA)"
