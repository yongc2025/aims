#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
bash scripts/linux/stop-aims.sh "$@"
