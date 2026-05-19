// targets.js — shared registry of agent platforms we install into.
// Each target describes where its skill directory lives and how to detect
// whether the platform is installed on this machine.

const os = require('os');
const path = require('path');
const fs = require('fs');

const HOME = os.homedir();
const SKILL_NAME = 'gtm-mavericks';

// Order matters — Claude Code first because it's the canonical home.
const TARGETS = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    skillsDir: path.join(HOME, '.claude', 'skills'),
    // Platform is "installed" if its config dir exists.
    detectDir: path.join(HOME, '.claude'),
    docs: 'https://docs.claude.com/en/docs/claude-code/skills',
  },
  {
    id: 'claude-code-plugins',
    name: 'Claude Code (plugins / marketplace)',
    // Plugins live alongside skills; we drop a link so marketplace-discovered
    // installs end up in the same place.
    skillsDir: path.join(HOME, '.claude', 'plugins'),
    detectDir: path.join(HOME, '.claude', 'plugins'),
    // Only install here if the plugins dir already exists — never create it.
    onlyIfExists: true,
    docs: 'https://docs.claude.com/en/docs/claude-code/plugins',
  },
  {
    id: 'codex',
    name: 'OpenAI Codex CLI',
    skillsDir: path.join(HOME, '.codex', 'skills'),
    detectDir: path.join(HOME, '.codex'),
    docs: 'https://github.com/openai/codex',
  },
  {
    id: 'gemini',
    name: 'Gemini CLI',
    skillsDir: path.join(HOME, '.gemini', 'skills'),
    detectDir: path.join(HOME, '.gemini'),
    docs: 'https://github.com/google-gemini/gemini-cli',
  },
  {
    id: 'opencode',
    name: 'OpenCode',
    // OpenCode (sst/opencode) reads from XDG-style config dirs.
    skillsDir: path.join(HOME, '.config', 'opencode', 'skills'),
    detectDir: path.join(HOME, '.config', 'opencode'),
    docs: 'https://github.com/sst/opencode',
  },
];

// Resolve which targets to install into.
//   GTM_INSTALL_TARGETS=none            → skip all
//   GTM_INSTALL_TARGETS=claude-code     → only Claude Code (comma-separated for multiple)
//   GTM_INSTALL_TARGETS=all             → all known targets, even if not detected
//   (unset)                              → auto: install to every detected target
function resolveTargets() {
  const env = (process.env.GTM_INSTALL_TARGETS || '').trim().toLowerCase();

  if (env === 'none') return [];
  if (env === 'all')  return TARGETS;

  if (env) {
    const ids = env.split(',').map(s => s.trim());
    return TARGETS.filter(t => ids.includes(t.id));
  }

  // Auto-detect
  return TARGETS.filter(t => {
    try { return fs.statSync(t.detectDir).isDirectory(); }
    catch { return false; }
  });
}

module.exports = { TARGETS, SKILL_NAME, resolveTargets };
