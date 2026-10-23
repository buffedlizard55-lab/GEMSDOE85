#!/usr/bin/env bash
# Session environment bootstrap.
#
# The arena snapshot does not persist dot-directories (.venv/) or git-ignored data folders
# (data/scored/, data/registry_rasters/), so both are rebuilt here from the SHA-256-pinned
# manifest.  The virtualenv lives OUTSIDE the repo (in /home/user/g85env) because a
# directory literally named ".venv" is excluded from snapshots.
#
#   bash scripts/session_setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${G85_VENV:-/home/user/g85env}"
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
  echo "[setup] creating venv at $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet -r "$ROOT/requirements-lock.txt"
fi
echo "[setup] python: $("$PY" -c 'import rasterio,numpy,scipy;print(rasterio.__version__)')"

cd "$ROOT"

if [ ! -f data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif ]; then
  echo "[setup] restoring manifest group: scored"
  "$PY" scripts/restore_data.py --groups scored
fi

if [ ! -f data/registry_rasters/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif ]; then
  echo "[setup] restoring registry control rasters (17)"
  "$PY" scripts/build_registry.py
fi

echo "[setup] ok"
