#!/usr/bin/env bash
# register_workflows.sh -- upsert all gtm-mavericks workflow definitions into Conductor.
#
# Uses `PUT /api/metadata/workflow` with a JSON array (the only Conductor endpoint that
# reliably upserts; the POST /metadata/workflow path errors with HTTP 500 "already exists"
# even with ?overwrite=true on OSS Conductor).
#
# Idempotent. Works against OSS Conductor (no auth) and Orkes Cloud (auth-key/secret).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WFDIR="$SCRIPT_DIR/../references/workflow-definitions"

ok()   { printf "  \033[32m[ok]\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m[warn]\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m[fail]\033[0m %s\n" "$1"; }
info() { printf "  \033[36m[info]\033[0m %s\n" "$1"; }

echo "gtm-mavericks: register workflows"
echo "----------------------------------"

if [ -z "${CONDUCTOR_SERVER_URL:-}" ]; then
  fail "CONDUCTOR_SERVER_URL not set. Example: export CONDUCTOR_SERVER_URL=http://localhost:8080/api"
  exit 1
fi
ok "CONDUCTOR_SERVER_URL: $CONDUCTOR_SERVER_URL"

# Mint a token if auth credentials are present (commercial Orkes); skip for OSS.
AUTH_HEADER=""
if [ -n "${CONDUCTOR_AUTH_KEY:-}" ] && [ -n "${CONDUCTOR_AUTH_SECRET:-}" ]; then
  TOKEN_RESP=$(curl -fsS -X POST -H "Content-Type: application/json" \
    -d "{\"keyId\":\"$CONDUCTOR_AUTH_KEY\",\"keySecret\":\"$CONDUCTOR_AUTH_SECRET\"}" \
    "$CONDUCTOR_SERVER_URL/token" 2>/dev/null) || {
      warn "Failed to mint auth token; proceeding without auth (OSS Conductor)."
    }
  if [ -n "$TOKEN_RESP" ]; then
    TOKEN=$(printf "%s" "$TOKEN_RESP" | node -e 'let s=""; process.stdin.on("data", d => s += d); process.stdin.on("end", () => { try { process.stdout.write(JSON.parse(s).token || ""); } catch (_) {} });')
    if [ -n "$TOKEN" ]; then
      AUTH_HEADER="-H X-Authorization:$TOKEN"
      ok "Auth token minted"
    fi
  fi
else
  info "No CONDUCTOR_AUTH_KEY/SECRET set; assuming OSS Conductor (no auth)."
fi

for f in discovery_new_product.json discovery_reposition.json discovery_campaign.json gtm_mavericks_v1.json; do
  path="$WFDIR/$f"
  if [ ! -f "$path" ]; then
    fail "Workflow definition missing: $path"
    exit 1
  fi
  name=$(node -e 'const fs = require("fs"); const wf = JSON.parse(fs.readFileSync(process.argv[1], "utf8")); process.stdout.write(wf.name);' "$path")
  version=$(node -e 'const fs = require("fs"); const wf = JSON.parse(fs.readFileSync(process.argv[1], "utf8")); process.stdout.write(String(wf.version || 1));' "$path")
  info "Registering $name v$version..."
  # Stream the JSON (wrapped in a 1-element array, per the PUT endpoint contract)
  # via stdin rather than `-d "[$(cat ...)]"` — the latter hits ARG_MAX on Linux
  # for the ~297KB main workflow file ("Argument list too long").
  RESPONSE=$(node -e 'const fs = require("fs"); const wf = JSON.parse(fs.readFileSync(process.argv[1], "utf8")); process.stdout.write(JSON.stringify([wf]));' "$path" \
    | curl -fsS -w "\n%{http_code}" -X PUT $AUTH_HEADER -H "Content-Type: application/json" \
        --data-binary @- \
        "$CONDUCTOR_SERVER_URL/metadata/workflow") || {
      fail "$name v$version: registration failed"
      echo "$RESPONSE"
      exit 1
    }
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Registered: $name v$version"
  else
    fail "$name v$version: HTTP $HTTP_CODE"
    echo "$RESPONSE" | head -n -1
    exit 1
  fi
done

echo "----------------------------------"
ok "Workflow registration complete."
