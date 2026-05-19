#!/usr/bin/env node
// postinstall.js — runs automatically after `npm install -g @conductor-skills/gtm`.
//
// Detects which agent platforms are installed on this machine (Claude Code,
// Codex, Gemini CLI, OpenCode, …) and symlinks the skill into each one's
// skills directory.
//
// Override behavior with the GTM_INSTALL_TARGETS env var:
//   GTM_INSTALL_TARGETS=none           → skip all auto-install
//   GTM_INSTALL_TARGETS=claude-code    → only Claude Code (comma-separated for multiple)
//   GTM_INSTALL_TARGETS=all            → install into every known target, even undetected ones
//
// Always idempotent: existing symlinks are replaced cleanly. Never blows away a
// non-symlink directory at the target — it warns and continues.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { resolveTargets, TARGETS, SKILL_NAME } = require('./targets');

const PACKAGE_ROOT = path.resolve(__dirname, '..');

const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const RED = '\x1b[31m';
const DIM = '\x1b[2m';
const RESET = '\x1b[0m';

function ok(msg)   { console.log(`  ${GREEN}[ok]${RESET}   ${msg}`); }
function info(msg) { console.log(`  ${CYAN}[info]${RESET} ${msg}`); }
function warn(msg) { console.log(`  ${YELLOW}[warn]${RESET} ${msg}`); }
function fail(msg) { console.log(`  ${RED}[fail]${RESET} ${msg}`); }

function installInto(target) {
  const targetPath = path.join(target.skillsDir, SKILL_NAME);

  // For targets with onlyIfExists: don't create the skills dir if missing
  if (target.onlyIfExists && !fs.existsSync(target.skillsDir)) {
    return { status: 'skipped', reason: 'parent dir missing' };
  }

  try {
    fs.mkdirSync(target.skillsDir, { recursive: true });
  } catch (err) {
    return { status: 'failed', reason: `mkdir ${target.skillsDir}: ${err.message}` };
  }

  let existing = null;
  try { existing = fs.lstatSync(targetPath); } catch (_) {}

  if (existing) {
    if (existing.isSymbolicLink()) {
      // Re-point if it doesn't already point at us
      const current = fs.readlinkSync(targetPath);
      if (current === PACKAGE_ROOT) {
        return { status: 'already', reason: targetPath };
      }
      fs.unlinkSync(targetPath);
    } else if (existing.isDirectory()) {
      return {
        status: 'conflict',
        reason: `non-symlink directory exists at ${targetPath}; leave alone`,
      };
    } else {
      fs.unlinkSync(targetPath);
    }
  }

  try {
    const linkType = process.platform === 'win32' ? 'junction' : 'dir';
    fs.symlinkSync(PACKAGE_ROOT, targetPath, linkType);
    return { status: 'linked', path: targetPath };
  } catch (err) {
    return { status: 'failed', reason: err.message };
  }
}

console.log('');
console.log(`Installing ${SKILL_NAME} into detected agent platforms...`);
console.log(`${DIM}(override with GTM_INSTALL_TARGETS=none|all|<id,id,...>)${RESET}`);
console.log('');

const targets = resolveTargets();

if (targets.length === 0) {
  if ((process.env.GTM_INSTALL_TARGETS || '').toLowerCase() === 'none') {
    info('Auto-install disabled (GTM_INSTALL_TARGETS=none).');
  } else {
    warn('No supported agent platforms detected on this machine.');
    info('To install manually, symlink the package into your agent\'s skills directory:');
    console.log('');
    for (const t of TARGETS) {
      console.log(`    ${t.name}:  ln -s ${PACKAGE_ROOT} ${path.join(t.skillsDir, SKILL_NAME)}`);
    }
  }
  console.log('');
  process.exit(0);
}

const results = [];
for (const target of targets) {
  const result = installInto(target);
  results.push({ target, result });

  switch (result.status) {
    case 'linked':
      ok(`${target.name.padEnd(36)} → ${result.path}`);
      break;
    case 'already':
      info(`${target.name.padEnd(36)} → already linked (${result.reason})`);
      break;
    case 'skipped':
      info(`${target.name.padEnd(36)} → skipped (${result.reason})`);
      break;
    case 'conflict':
      warn(`${target.name.padEnd(36)} → ${result.reason}`);
      break;
    case 'failed':
      fail(`${target.name.padEnd(36)} → ${result.reason}`);
      break;
  }
}

console.log('');
const linked = results.filter(r => ['linked', 'already'].includes(r.result.status)).length;
const total  = results.length;
console.log(`${GREEN}Installed into ${linked}/${total} platform(s).${RESET}`);

console.log('');
console.log('Next steps:');
console.log('');
console.log('  1. Set your Conductor server URL (add to ~/.zshrc to persist):');
console.log(`       ${CYAN}export CONDUCTOR_SERVER_URL=http://localhost:8080/api${RESET}`);
console.log('');
console.log('  2. Bootstrap deps and register workflows:');
console.log(`       ${CYAN}gtm-install${RESET}`);
console.log('');
console.log('  3. Open your agent of choice and ask:');
console.log(`       ${CYAN}"let's run a gtm for a new product idea"${RESET}`);
console.log('');
console.log(`${DIM}Source: ${PACKAGE_ROOT}${RESET}`);
console.log(`${DIM}Docs: ${path.join(PACKAGE_ROOT, 'README.md')}${RESET}`);
console.log('');

// Always exit 0 — never let a postinstall failure break npm install.
process.exit(0);
