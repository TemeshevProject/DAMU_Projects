#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="${PATH}:${HOME}/.local/bin}"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
streamlit run dashboard/app.py --server.headless true --browser.gatherUsageStats false "$@"
