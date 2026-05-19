#!/usr/bin/env node
// install.js — the `gtm-install` command.
// Bootstraps Conductor: runs install_check.sh (interactive), then register_workflows.sh.
// Safe to re-run.

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const SCRIPTS_DIR = path.join(PACKAGE_ROOT, 'scripts');
const INSTALL_CHECK = path.join(SCRIPTS_DIR, 'install_check.sh');
const REGISTER = path.join(SCRIPTS_DIR, 'register_workflows.sh');

const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const CYAN = '\x1b[36m';
const RESET = '\x1b[0m';

function header(msg) {
  console.log('');
  console.log(`${CYAN}━━ ${msg} ━━${RESET}`);
  console.log('');
}

function run(script, args = []) {
  if (!fs.existsSync(script)) {
    console.log(`${RED}Missing script: ${script}${RESET}`);
    process.exit(1);
  }
  // Ensure executable bit
  try { fs.chmodSync(script, 0o755); } catch (_) {}
  const result = spawnSync('bash', [script, ...args], { stdio: 'inherit' });
  return result.status;
}

header('Step 1/2: Verify and install dependencies');
const checkStatus = run(INSTALL_CHECK);
if (checkStatus !== 0) {
  console.log('');
  console.log(`${RED}Dependency check failed.${RESET} Fix the items above and re-run: gtm-install`);
  process.exit(checkStatus);
}

header('Step 2/2: Register workflows with Conductor');
const regStatus = run(REGISTER);
if (regStatus !== 0) {
  console.log('');
  console.log(`${RED}Workflow registration failed.${RESET}`);
  process.exit(regStatus);
}

console.log('');
console.log(`${GREEN}All set.${RESET} The gtm-mavericks skill is ready to use in Claude Code.`);
console.log('');
console.log('Try opening Claude Code and saying:');
console.log(`  ${CYAN}"let's run a gtm for a new product idea I have"${RESET}`);
console.log('');
