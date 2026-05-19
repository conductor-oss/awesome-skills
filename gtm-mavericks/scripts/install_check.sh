#!/usr/bin/env bash
# install_check.sh — verify and optionally install prerequisites for gtm-mavericks
#
# Modes:
#   install_check.sh                    # interactive: prompt before installing missing deps
#   install_check.sh --non-interactive  # check only, never prompt/install (exit non-zero on missing)
#   install_check.sh --auto-install     # install everything possible without prompting
#
# Exit codes:
#   0  — all required prerequisites are in place
#   1  — one or more required prerequisites are missing or could not be installed
#
# Required: npm, conductor CLI, CONDUCTOR_SERVER_URL, 6 personas, 4 workflow JSONs
# Optional (warn-only): pandoc, marp

set -u

MODE="interactive"
for arg in "$@"; do
  case "$arg" in
    --non-interactive) MODE="check-only" ;;
    --auto-install)    MODE="auto-install" ;;
    --help|-h)
      sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
  esac
done

# If stdin isn't a tty in interactive mode, downgrade to check-only
if [ "$MODE" = "interactive" ] && [ ! -t 0 ]; then
  MODE="check-only"
fi

ok()   { printf "  \033[32m[ok]\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m[warn]\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m[fail]\033[0m %s\n" "$1"; }
info() { printf "  \033[36m[info]\033[0m %s\n" "$1"; }

# prompt_install <human-name> <install-command>
# Returns 0 if install succeeded, 1 if declined or failed.
prompt_install() {
  local name="$1"
  local cmd="$2"
  case "$MODE" in
    auto-install)
      info "Installing $name automatically..."
      if eval "$cmd"; then
        return 0
      else
        fail "$name install failed."
        return 1
      fi
      ;;
    check-only)
      info "Skipping install ($MODE mode). Install manually: $cmd"
      return 1
      ;;
    interactive)
      printf "  Install %s now? [y/N] " "$name"
      read -r response
      case "$response" in
        [yY]|[yY][eE][sS])
          info "Installing $name..."
          if eval "$cmd"; then
            return 0
          else
            fail "$name install failed. Try manually: $cmd"
            return 1
          fi
          ;;
        *)
          info "Skipped. Install manually when ready: $cmd"
          return 1
          ;;
      esac
      ;;
  esac
}

HARD_FAILS=0

echo "gtm-mavericks install check (mode: $MODE)"
echo "------------------------------------------"

# --- 1. npm (prerequisite for conductor CLI and marp) ---
if ! command -v npm >/dev/null 2>&1; then
  fail "npm not found. Node.js + npm is required for conductor CLI and marp."
  if [ "$(uname)" = "Darwin" ]; then
    info "Install: brew install node"
  elif command -v apt-get >/dev/null 2>&1; then
    info "Install: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs"
  else
    info "Install Node from https://nodejs.org"
  fi
  fail "Aborting check — npm is required to bootstrap dependencies."
  exit 1
fi
ok "npm: $(npm --version 2>/dev/null)"

# --- 2. conductor CLI (REQUIRED; auto-install offered) ---
if command -v conductor >/dev/null 2>&1; then
  ok "conductor CLI: $(conductor --version 2>/dev/null | head -1)"
else
  warn "conductor CLI not found."
  if prompt_install "conductor CLI" "npm install -g @conductor-oss/conductor-cli"; then
    # Re-check PATH (npm -g sometimes installs to a location not on PATH)
    hash -r 2>/dev/null || true
    if command -v conductor >/dev/null 2>&1; then
      ok "conductor CLI installed: $(conductor --version 2>/dev/null | head -1)"
    else
      fail "conductor CLI installed but not on PATH. Check 'npm config get prefix' and add its bin/ to PATH."
      HARD_FAILS=$((HARD_FAILS + 1))
    fi
  else
    fail "conductor CLI is required."
    HARD_FAILS=$((HARD_FAILS + 1))
  fi
fi

# --- 3. CONDUCTOR_SERVER_URL (REQUIRED; cannot auto-set) ---
if [ -n "${CONDUCTOR_SERVER_URL:-}" ]; then
  ok "CONDUCTOR_SERVER_URL: $CONDUCTOR_SERVER_URL"
else
  fail "CONDUCTOR_SERVER_URL not set."
  info "Set it for the current shell:  export CONDUCTOR_SERVER_URL=http://localhost:8080/api"
  info "To persist, add the line to ~/.zshrc or ~/.bashrc."
  HARD_FAILS=$((HARD_FAILS + 1))
fi

# --- 4. pandoc (OPTIONAL; warn-only; auto-install offered) ---
if command -v pandoc >/dev/null 2>&1; then
  ok "pandoc: $(pandoc --version 2>/dev/null | head -1)"
else
  warn "pandoc not found — PDF output will be skipped."
  if [ "$(uname)" = "Darwin" ]; then
    PANDOC_CMD="brew install pandoc"
  elif command -v apt-get >/dev/null 2>&1; then
    PANDOC_CMD="sudo apt-get install -y pandoc"
  else
    PANDOC_CMD=""
  fi
  if [ -n "$PANDOC_CMD" ]; then
    if prompt_install "pandoc" "$PANDOC_CMD"; then
      hash -r 2>/dev/null || true
      command -v pandoc >/dev/null 2>&1 && ok "pandoc installed: $(pandoc --version | head -1)" || warn "pandoc install ran but binary not on PATH."
    fi
  else
    info "Install pandoc manually for your platform: https://pandoc.org/installing.html"
  fi
fi

# --- 5. marp CLI (OPTIONAL; warn-only; auto-install offered) ---
if command -v marp >/dev/null 2>&1; then
  ok "marp: $(marp --version 2>/dev/null | head -1)"
else
  warn "marp CLI not found — slide output will be skipped."
  if prompt_install "marp CLI" "npm install -g @marp-team/marp-cli"; then
    hash -r 2>/dev/null || true
    command -v marp >/dev/null 2>&1 && ok "marp installed: $(marp --version | head -1)" || warn "marp install ran but binary not on PATH."
  fi
fi

# --- 6. Persona files (REQUIRED; part of the skill, not externally installable) ---
PERSONAS_DIR="$(dirname "$0")/../references/personas"
PERSONA_COUNT=$(ls "$PERSONAS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$PERSONA_COUNT" = "6" ]; then
  ok "Persona library: 6 files found"
else
  fail "Persona library incomplete: expected 6 files, found $PERSONA_COUNT"
  HARD_FAILS=$((HARD_FAILS + 1))
fi

# --- 7. Workflow definitions (REQUIRED; part of the skill) ---
WFDIR="$(dirname "$0")/../references/workflow-definitions"
for f in gtm_mavericks_v1.json discovery_new_product.json discovery_reposition.json discovery_campaign.json; do
  if [ -f "$WFDIR/$f" ]; then
    if python3 -c "import json,sys; json.load(open('$WFDIR/$f'))" 2>/dev/null; then
      ok "Workflow definition parses: $f"
    else
      fail "Workflow definition invalid JSON: $f"
      HARD_FAILS=$((HARD_FAILS + 1))
    fi
  else
    fail "Workflow definition missing: $f"
    HARD_FAILS=$((HARD_FAILS + 1))
  fi
done

echo "------------------------------------------"
if [ "$HARD_FAILS" -gt 0 ]; then
  fail "$HARD_FAILS hard failure(s). Fix the above before running gtm-mavericks."
  exit 1
fi
ok "Ready to go."
