#!/usr/bin/env bash
# render_pdf.sh — render a gtm-mavericks run output to PDF via pandoc
# Usage: render_pdf.sh /path/to/.gtm/runs/<run-id>/
# Reads outputs/gtm-full.md, writes outputs/gtm-full.pdf

set -e

RUN_DIR="${1:?Usage: $0 <run-dir>}"
INPUT="$RUN_DIR/outputs/gtm-full.md"
OUTPUT="$RUN_DIR/outputs/gtm-full.pdf"

if [ ! -f "$INPUT" ]; then
  echo "[fail] No gtm-full.md found at $INPUT"
  exit 1
fi

if ! command -v pandoc >/dev/null 2>&1; then
  echo "[warn] pandoc not installed — skipping PDF render. Install: brew install pandoc"
  exit 0
fi

# Try xelatex first; fall back to weasyprint (HTML→PDF) if no LaTeX engine available
if command -v xelatex >/dev/null 2>&1; then
  pandoc "$INPUT" -o "$OUTPUT" --pdf-engine=xelatex
elif command -v weasyprint >/dev/null 2>&1; then
  pandoc "$INPUT" -o "$OUTPUT" --pdf-engine=weasyprint
else
  echo "[warn] No PDF engine found (need xelatex or weasyprint). Writing HTML instead."
  pandoc "$INPUT" -o "$RUN_DIR/outputs/gtm-full.html" --standalone
  exit 0
fi

echo "PDF written to: $OUTPUT"
