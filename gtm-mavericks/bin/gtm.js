#!/usr/bin/env node
// gtm.js — unified entry for the @conductor-skills/gtm package.
//
// One-command install via npx:
//   npx @conductor-skills/gtm                       # auto-detect + symlink into every installed agent
//   npx @conductor-skills/gtm --agent codex         # only into Codex CLI
//   npx @conductor-skills/gtm --agent claude-code,codex
//   npx @conductor-skills/gtm --agent all           # into every known agent (even undetected)
//   npx @conductor-skills/gtm --bootstrap           # symlink + run Conductor server setup + register workflows
//   npx @conductor-skills/gtm --bootstrap-only      # skip symlink; just bootstrap Conductor
//   npx @conductor-skills/gtm --uninstall           # remove every symlink
//   npx @conductor-skills/gtm --help
//
// Equivalent global-install flow:
//   npm install -g @conductor-skills/gtm   # postinstall auto-symlinks
//   gtm                                    # same as npx form
//   gtm-install                            # alias: --bootstrap
//   gtm-uninstall                          # alias: --uninstall

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { resolveTargets, TARGETS, SKILL_NAME } = require('./targets');

const PACKAGE_ROOT = path.resolve(__dirname, '..');

const G = '\x1b[32m', Y = '\x1b[33m', R = '\x1b[31m', C = '\x1b[36m', D = '\x1b[2m', X = '\x1b[0m';
const ok      = (m) => console.log(`  ${G}[ok]${X}   ${m}`);
const info    = (m) => console.log(`  ${C}[info]${X} ${m}`);
const warn    = (m) => console.log(`  ${Y}[warn]${X} ${m}`);
const fail    = (m) => console.log(`  ${R}[fail]${X} ${m}`);
const header  = (m) => { console.log(''); console.log(`${C}── ${m} ──${X}`); console.log(''); };

function parseArgs(argv) {
  const args = {
    agent: null,
    bootstrap: false,
    bootstrapOnly: false,
    uninstall: false,
    help: false,
    quiet: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h')         { args.help = true; }
    else if (a === '--bootstrap')             { args.bootstrap = true; }
    else if (a === '--bootstrap-only')        { args.bootstrapOnly = true; }
    else if (a === '--uninstall')             { args.uninstall = true; }
    else if (a === '--quiet')                 { args.quiet = true; }
    else if (a === '--agent')                 { args.agent = (argv[++i] || '').trim(); }
    else if (a.startsWith('--agent='))        { args.agent = a.slice('--agent='.length).trim(); }
    else {
      console.error(`unknown flag: ${a}\nrun with --help for usage`);
      process.exit(2);
    }
  }
  // Basename-based aliases — when invoked as gtm-install / gtm-uninstall,
  // imply the matching flag.
  const invokedAs = path.basename(process.argv[1] || '').toLowerCase();
  if (invokedAs === 'gtm-install') args.bootstrap = true;
  if (invokedAs === 'gtm-uninstall') args.uninstall = true;
  return args;
}

function showHelp() {
  console.log(`
@conductor-skills/gtm — GTM Mavericks installer

USAGE
  npx @conductor-skills/gtm [flags]

DEFAULT (no flags)
  Auto-detect installed coding agents (Claude Code, Codex CLI, Gemini CLI,
  OpenCode) and symlink the skill into each. Print next steps for setting up
  the Conductor server.

FLAGS
  --agent <id>        Install only into one agent. Valid IDs:
                      ${TARGETS.map(t => t.id).join(', ')}.
                      Comma-separated for multiple. "all" installs into every
                      known agent even if undetected.
  --bootstrap         After symlinking, run install_check.sh (Conductor server
                      setup, interactive) and register_workflows.sh.
  --bootstrap-only    Skip symlinking; only run the Conductor bootstrap. Use
                      when the skill is already installed but workflows need
                      re-registering (e.g., after an upgrade).
  --uninstall         Remove every gtm-mavericks symlink. Does not remove the
                      Conductor server, the conductor CLI, or any run data.
  --quiet             Less console chatter.
  --help, -h          Show this help.

EXAMPLES
  npx @conductor-skills/gtm                       # auto-detect + symlink
  npx @conductor-skills/gtm --agent codex         # only Codex CLI
  npx @conductor-skills/gtm --agent claude-code,codex
  npx @conductor-skills/gtm --bootstrap           # also bootstrap Conductor
  npx @conductor-skills/gtm --uninstall
`);
}

function installInto(target) {
  const targetPath = path.join(target.skillsDir, SKILL_NAME);

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
      const current = fs.readlinkSync(targetPath);
      if (current === PACKAGE_ROOT) return { status: 'already', path: targetPath };
      fs.unlinkSync(targetPath);
    } else if (existing.isDirectory()) {
      return { status: 'conflict', reason: `non-symlink dir at ${targetPath}; leaving alone` };
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

function runSymlinkInstall(args) {
  if (args.agent) process.env.GTM_INSTALL_TARGETS = args.agent;

  const targets = resolveTargets();

  if (!args.quiet) {
    header(`Installing ${SKILL_NAME} into agent platforms`);
  }

  if (targets.length === 0) {
    const env = (process.env.GTM_INSTALL_TARGETS || '').toLowerCase();
    if (env === 'none') {
      info('Auto-install disabled (GTM_INSTALL_TARGETS=none).');
    } else if (args.agent) {
      fail(`No targets matched --agent="${args.agent}". Valid IDs:`);
      for (const t of TARGETS) console.log(`    ${t.id.padEnd(22)} ${t.name}`);
      process.exit(1);
    } else {
      warn('No supported agent platforms detected on this machine.');
      info('To install manually, symlink the package into your agent\'s skills directory:');
      for (const t of TARGETS) {
        console.log(`    ${t.name}:  ln -s ${PACKAGE_ROOT} ${path.join(t.skillsDir, SKILL_NAME)}`);
      }
    }
    return { linked: 0, total: 0 };
  }

  let linked = 0;
  for (const target of targets) {
    const result = installInto(target);
    const label = target.name.padEnd(36);
    switch (result.status) {
      case 'linked':   ok(`${label} → ${result.path}`); linked++; break;
      case 'already':  info(`${label} → already linked`); linked++; break;
      case 'skipped':  info(`${label} → skipped (${result.reason})`); break;
      case 'conflict': warn(`${label} → ${result.reason}`); break;
      case 'failed':   fail(`${label} → ${result.reason}`); break;
    }
  }

  console.log('');
  console.log(`${G}Installed into ${linked}/${targets.length} platform(s).${X}`);
  return { linked, total: targets.length };
}

function runBootstrap() {
  header('Bootstrap Conductor server + register workflows');
  const SCRIPTS_DIR = path.join(PACKAGE_ROOT, 'scripts');
  const INSTALL_CHECK = path.join(SCRIPTS_DIR, 'install_check.sh');
  const REGISTER = path.join(SCRIPTS_DIR, 'register_workflows.sh');

  for (const script of [INSTALL_CHECK, REGISTER]) {
    if (!fs.existsSync(script)) {
      fail(`Missing script: ${script}`);
      process.exit(1);
    }
    try { fs.chmodSync(script, 0o755); } catch (_) {}
  }

  let r = spawnSync('bash', [INSTALL_CHECK], { stdio: 'inherit' });
  if (r.status !== 0) {
    console.log('');
    fail('install_check.sh failed. Fix the items above and re-run.');
    process.exit(r.status || 1);
  }

  r = spawnSync('bash', [REGISTER], { stdio: 'inherit' });
  if (r.status !== 0) {
    console.log('');
    fail('register_workflows.sh failed.');
    process.exit(r.status || 1);
  }

  console.log('');
  console.log(`${G}Bootstrap complete.${X}`);
}

function runUninstall() {
  header(`Removing ${SKILL_NAME} symlinks`);
  let removed = 0, absent = 0, kept = 0;
  for (const target of TARGETS) {
    const targetPath = path.join(target.skillsDir, SKILL_NAME);
    let stat = null;
    try { stat = fs.lstatSync(targetPath); } catch (_) {}
    if (!stat) { absent++; continue; }
    if (stat.isSymbolicLink()) {
      fs.unlinkSync(targetPath);
      ok(`Removed: ${targetPath}  ${D}(${target.name})${X}`);
      removed++;
    } else {
      warn(`${targetPath} is a real directory (not a symlink). Leaving alone.`);
      kept++;
    }
  }
  console.log('');
  console.log(`Removed ${removed} symlink(s); ${absent} platform(s) had no install; ${kept} non-symlink targets left alone.`);
  console.log('');
  console.log(`Run ${C}npm uninstall -g @conductor-skills/gtm${X} to remove the package itself.`);
  console.log(`Run data in any project's .gtm/runs/ and gtm-output/ folders is preserved.`);
}

function showNextSteps(args) {
  if (args.quiet) return;
  console.log('');
  console.log('NEXT STEPS:');
  console.log('');
  console.log(`  1. ${C}npx @conductor-skills/gtm --bootstrap${X}`);
  console.log('     (one-time: sets up the Conductor server + registers workflows)');
  console.log('');
  console.log('  2. Open your agent and ask:');
  console.log(`     ${C}"let's run a gtm for a new product idea"${X}`);
  console.log('');
  console.log(`${D}Skill source: ${PACKAGE_ROOT}${X}`);
  console.log(`${D}Docs: ${path.join(PACKAGE_ROOT, 'README.md')}${X}`);
  console.log('');
}

// --- main ---
const args = parseArgs(process.argv.slice(2));

if (args.help) { showHelp(); process.exit(0); }
if (args.uninstall) { runUninstall(); process.exit(0); }

if (!args.bootstrapOnly) {
  runSymlinkInstall(args);
}

if (args.bootstrap || args.bootstrapOnly) {
  runBootstrap();
} else {
  showNextSteps(args);
}

process.exit(0);
