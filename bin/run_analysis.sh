#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
RUN_DATE="$(date +%Y-%m-%d)"
LOG_FILE="$LOG_DIR/analysis_${RUN_DATE}.log"
ENV_FILE="$HOME/.myenv"

mkdir -p "$LOG_DIR"

# Ensure we run from the repository root so Python scripts use repository-relative paths
cd "$ROOT_DIR" || { echo "ERROR: failed to cd to $ROOT_DIR"; exit 1; }

# Redirect all output to dated logfile.
exec >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] analysis run started"

if [[ ! -f "$ENV_FILE" ]]; then
	echo "ERROR: Environment file not found: $ENV_FILE"
	exit 1
fi

on_error() {
	local exit_code=$?
	echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: analysis run failed (exit code: ${exit_code})"
}
trap on_error ERR

# Export all variables defined in .myenv for child processes (cron-safe).
set -a
. "$ENV_FILE"
set +a

: "${MYSQL_USER:?MYSQL_USER is not set in $ENV_FILE}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is not set in $ENV_FILE}"

python3 "$ROOT_DIR/bin/2_summarize_scan.py"
python3 "$ROOT_DIR/bin/3_mysql_run.py"
python3 "$ROOT_DIR/bin/4_plot_user.py"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] analysis run completed successfully"
