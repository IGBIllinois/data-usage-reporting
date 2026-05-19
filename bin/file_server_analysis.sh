#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$ROOT_DIR/config_file-server"
LOG_DIR="$ROOT_DIR/logs"
RUN_DATE="$(date +%Y%m%d)"
LOG_FILE="$LOG_DIR/file_summarize_${RUN_DATE}.log"

mkdir -p "$LOG_DIR"

# Redirect all script output to logfile only.
exec >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] file-server analysis started"

on_error() {
	local exit_code=$?
	echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: file-server analysis failed (exit code: ${exit_code})"
}
trap on_error ERR

python3 -u "$ROOT_DIR/bin/2_summarize_scan.py" --config-dir "$CONFIG_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] file-server analysis completed successfully"