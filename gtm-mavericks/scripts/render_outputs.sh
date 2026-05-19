#!/usr/bin/env bash
# render_outputs.sh — render a completed GTM Mavericks workflow's bundle to markdown + PDF.
#
# Usage:
#   ./render_outputs.sh <workflow_id> [output_dir]
#   ./render_outputs.sh --run-id <run_id>     # reads .gtm/runs/<run-id>/state.json
#
# Env required:
#   CONDUCTOR_SERVER_URL
#   Either CONDUCTOR_AUTH_KEY + CONDUCTOR_AUTH_SECRET, or CONDUCTOR_PROFILE

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/render_outputs.py" "$@"
