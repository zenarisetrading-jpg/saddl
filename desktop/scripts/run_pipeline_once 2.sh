#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_pipeline_once.sh                # defaults to yesterday UTC
#   ./scripts/run_pipeline_once.sh 2026-02-15    # explicit date

TARGET_DATE="${1:-$(python3 - <<'PY'
from datetime import datetime, timedelta
print((datetime.utcnow().date() - timedelta(days=1)).strftime('%Y-%m-%d'))
PY
)}"

echo "Running SP-API pipeline for date: ${TARGET_DATE}"

python3 - <<PY
from pipeline.runner import run_single_date
from pipeline.config import get_config

config = get_config()
written = run_single_date('${TARGET_DATE}', config)
print(f'Completed. Rows written: {written}')
PY
