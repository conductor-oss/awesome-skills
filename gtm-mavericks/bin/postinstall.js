#!/usr/bin/env node
// postinstall.js — auto-runs after `npm install -g @conductor-skills/gtm`.
// Delegates to bin/gtm.js (default behavior: auto-detect agents + symlink + print next steps).
//
// Skips itself under npx (`npm_command === 'exec'`) so flags like `--agent codex`
// passed to the bin aren't pre-empted by an unconditional auto-symlink.
//
// Always exits 0 — never break `npm install`.

if (process.env.npm_command === 'exec') {
  // npx context: the bin invocation (with the user's flags) will handle install.
  process.exit(0);
}

const { spawnSync } = require('child_process');
const path = require('path');

spawnSync('node', [path.join(__dirname, 'gtm.js')], { stdio: 'inherit' });
process.exit(0);
