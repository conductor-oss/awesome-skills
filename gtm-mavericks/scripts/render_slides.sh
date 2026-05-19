#!/usr/bin/env bash
# render_slides.sh — render a gtm-mavericks run output to slides via Marp
# Usage: render_slides.sh /path/to/.gtm/runs/<run-id>/
# Reads outputs/gtm-deck.md, writes outputs/gtm-deck.pdf and gtm-deck.html

set -e

RUN_DIR="${1:?Usage: $0 <run-dir>}"
INPUT="$RUN_DIR/outputs/gtm-deck.md"

if [ ! -f "$INPUT" ]; then
  echo "[fail] No gtm-deck.md found at $INPUT"
  exit 1
fi

if ! command -v marp >/dev/null 2>&1; then
  echo "[warn] marp not installed — skipping slide render. Install: npm install -g @marp-team/marp-cli"
  exit 0
fi

marp "$INPUT" -o "$RUN_DIR/outputs/gtm-deck.pdf" --allow-local-files
marp "$INPUT" -o "$RUN_DIR/outputs/gtm-deck.html" --allow-local-files

echo "Slides written to: $RUN_DIR/outputs/gtm-deck.pdf and gtm-deck.html"
