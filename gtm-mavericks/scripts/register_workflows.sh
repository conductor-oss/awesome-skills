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
    TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))")
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
  name=$(python3 -c "import json; print(json.load(open('$path'))['name'])")
  version=$(python3 -c "import json; print(json.load(open('$path')).get('version', 1))")
  info "Registering $name v$version..."
  RESPONSE=$(curl -fsS -w "\n%{http_code}" -X PUT $AUTH_HEADER -H "Content-Type: application/json" \
    -d "[$(cat "$path")]" \
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
