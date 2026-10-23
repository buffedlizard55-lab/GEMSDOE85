#!/usr/bin/env bash
# Autonomous downloader & SHA-256 verifier for DOE GEMS Prize #306 competition rasters
# and official public-domain USGS 3DEP (1 m LiDAR & 10 m seamless DEM), USGS GeoDAWN,
# DOE GDR #1391 INGENIOUS geothermometry/probes/sinter, and USGS ScienceBase heat flow.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${GEMS_DATA_DIR:-${ROOT}/data/raw}"
PYTHON_BIN="${ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
    PYTHON_BIN="python3"
fi

echo "[1/2] Restoring & SHA-256 verifying core competition + external datasets into ${TARGET_DIR}..."
"${PYTHON_BIN}" "${ROOT}/scripts/restore_data.py" --target-dir "${TARGET_DIR}"

echo "[2/2] Restoring & SHA-256 verifying 13 USGS 3DEP 10 m DEM channels + GDR #1391 thermal layers..."
"${PYTHON_BIN}" "${ROOT}/scripts/prepare_data.py" --data-dir "${TARGET_DIR}" --verify-only

echo "[OK] All core & external public-domain geophysical datasets placed and SHA-256 verified."
