#!/usr/bin/env bash
# run_e2e.sh — execute an end-to-end gtm-mavericks scenario and grade the output.
#
# Usage:  ./run_e2e.sh path/to/scenario.yaml
#
# Steps:
#   1. Parse the YAML scenario → intake.json
#   2. Start the workflow via conductor CLI
#   3. Poll for completion (workflow runs 30-60 min)
#   4. Fetch the bundle
#   5. Run tier-2 (bundle) evals against the bundle
#
# Requires: conductor CLI, CONDUCTOR_SERVER_URL set, python3 with pyyaml + anthropic.

set -e

SCENARIO="${1:?Usage: $0 <scenario.yaml>}"
SKILL_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SCENARIO_NAME="$(basename "$SCENARIO" .yaml)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$SKILL_DIR/evals/results/e2e-${SCENARIO_NAME}-${TIMESTAMP}"

mkdir -p "$RUN_DIR"

GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"; RED="\033[31m"; RESET="\033[0m"

echo "${CYAN}━━━━ E2E run: $SCENARIO_NAME ━━━━${RESET}"
echo "  Output dir: $RUN_DIR"
echo ""

# --- 1. Convert scenario YAML to intake JSON ---
INTAKE_JSON="$RUN_DIR/intake.json"
python3 - <<EOF
import yaml, json, sys
with open("$SCENARIO") as f:
    scenario = yaml.safe_load(f)
# Strip eval-only fields
scenario.pop("expectations", None)
scenario.pop("name", None)
with open("$INTAKE_JSON", "w") as f:
    json.dump(scenario, f, indent=2)
print(f"  ${CYAN}[ok]${RESET}   Wrote intake to $INTAKE_JSON")
EOF

# --- 2. Start workflow ---
if ! command -v conductor >/dev/null 2>&1; then
  echo "${RED}[fail] conductor CLI not found. Run: gtm-install${RESET}"
  exit 1
fi
if [ -z "${CONDUCTOR_SERVER_URL:-}" ]; then
  echo "${RED}[fail] CONDUCTOR_SERVER_URL not set${RESET}"
  exit 1
fi

echo "  ${CYAN}[info]${RESET} Starting workflow gtm_mavericks_v1..."
WORKFLOW_ID="$(conductor workflow start -w gtm_mavericks_v1 --version 1 -f "$INTAKE_JSON" 2>/dev/null | tail -1 | tr -d '"' | tr -d ' ')"

if [ -z "$WORKFLOW_ID" ]; then
  echo "${RED}[fail] Could not start workflow${RESET}"
  exit 1
fi

echo "  ${GREEN}[ok]${RESET}   Workflow started: $WORKFLOW_ID"
echo "$WORKFLOW_ID" > "$RUN_DIR/workflow_id"

# --- 3. Poll for completion ---
echo "  ${CYAN}[info]${RESET} Polling for completion (this typically takes 30-60 min)..."
POLL_START=$(date +%s)
while true; do
  STATUS="$(conductor workflow status "$WORKFLOW_ID" 2>/dev/null | tail -1 | tr -d '"' | tr -d ' ')"
  ELAPSED=$(( $(date +%s) - POLL_START ))
  MM=$(( ELAPSED / 60 ))
  SS=$(( ELAPSED % 60 ))

  printf "\r  ${CYAN}[info]${RESET} status=%-12s  elapsed=%02d:%02d  " "$STATUS" "$MM" "$SS"

  case "$STATUS" in
    COMPLETED) echo ""; echo "  ${GREEN}[ok]${RESET}   Workflow completed in ${MM}m${SS}s"; break ;;
    FAILED|TERMINATED|TIMED_OUT)
      echo ""; echo "${RED}[fail] Workflow ended with status: $STATUS${RESET}"
      conductor workflow get-execution "$WORKFLOW_ID" -c > "$RUN_DIR/failed-execution.json"
      echo "       Details: $RUN_DIR/failed-execution.json"
      exit 1
      ;;
  esac
  sleep 30
done

# --- 4. Fetch bundle ---
echo "  ${CYAN}[info]${RESET} Fetching bundle..."
conductor workflow get-execution "$WORKFLOW_ID" -c > "$RUN_DIR/execution.json"
python3 - <<EOF
import json
with open("$RUN_DIR/execution.json") as f:
    exec_data = json.load(f)
# Final bundle is under workflow.output.final_bundle in most workflow versions
bundle = exec_data.get("output", {}).get("final_bundle") or exec_data.get("finalOutput", {}).get("final_bundle")
if not bundle:
    # Fallback: dig through tasks for bundle_artifacts output
    for t in exec_data.get("tasks", []):
        if t.get("taskReferenceName") == "bundle_artifacts":
            bundle = (t.get("outputData") or {}).get("result")
            break
if not bundle:
    print("${RED}[fail] No bundle found in workflow output${RESET}"); exit(1)
with open("$RUN_DIR/bundle.json", "w") as f:
    json.dump(bundle, f, indent=2)
print(f"  ${GREEN}[ok]${RESET}   Bundle written to $RUN_DIR/bundle.json")
EOF

# --- 5. Run bundle evals ---
echo ""
echo "${CYAN}━━━━ Running bundle evals ━━━━${RESET}"
python3 "$SKILL_DIR/evals/runner.py" --tier bundle --bundle "$RUN_DIR/bundle.json"
RUNNER_EXIT=$?

echo ""
if [ "$RUNNER_EXIT" -eq 0 ]; then
  echo "${GREEN}━━━━ E2E PASS: $SCENARIO_NAME ━━━━${RESET}"
else
  echo "${YELLOW}━━━━ E2E completed but bundle has failures: $SCENARIO_NAME ━━━━${RESET}"
fi
echo "  Artifacts: $RUN_DIR/"
exit "$RUNNER_EXIT"
