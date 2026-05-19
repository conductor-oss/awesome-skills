#!/usr/bin/env node
// uninstall.js — the `gtm-uninstall` command.
// Removes the skill symlink from every agent platform it was installed into.
// Does NOT uninstall the conductor CLI, pandoc, or marp.
// Does NOT remove your .gtm/runs/ or gtm-output/ data.

const fs = require('fs');
const path = require('path');
const { TARGETS, SKILL_NAME } = require('./targets');

const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const RESET = '\x1b[0m';

console.log('');

let removed = 0;
let absent = 0;
let kept = 0;

for (const target of TARGETS) {
  const targetPath = path.join(target.skillsDir, SKILL_NAME);
  let stat = null;
  try { stat = fs.lstatSync(targetPath); } catch (_) {}

  if (!stat) {
    absent++;
    continue;
  }

  if (stat.isSymbolicLink()) {
    fs.unlinkSync(targetPath);
    console.log(`  ${GREEN}[ok]${RESET}   Removed: ${targetPath}  ${YELLOW}(${target.name})${RESET}`);
    removed++;
  } else {
    console.log(`  ${YELLOW}[warn]${RESET} ${targetPath} is a real directory (not a symlink). Leaving alone.`);
    kept++;
  }
}

console.log('');
console.log(`Removed ${removed} symlink(s); ${absent} platform(s) had no install; ${kept} non-symlink targets left alone.`);
console.log('');
console.log(`Run ${CYAN}npm uninstall -g @conductor-skills/gtm${RESET} to remove the package itself.`);
console.log(`Run data in any project's .gtm/runs/ and gtm-output/ folders is preserved.`);
console.log('');
