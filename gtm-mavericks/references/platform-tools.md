# Platform tools — cross-agent compatibility

This skill is written using Claude Code's tool names in the `allowed-tools` frontmatter. The body uses generic shell commands and file I/O that work on every agent. If you're running this skill on a non-Claude platform, this table tells you which native tools to use for each operation the skill describes.

The skill never asks for a specific tool by name in the prose — it says things like "run this script" or "read the workflow execution JSON." Use whatever tool your platform exposes for that operation.

## Operations the skill needs

| Operation | Claude Code | OpenAI Codex CLI | Gemini CLI | OpenCode |
|---|---|---|---|---|
| Run a shell command | `Bash` | `shell` / direct shell exec | `run_shell_command` | shell exec |
| Read a file | `Read` | `shell` (cat) or built-in read | `read_file` | built-in read |
| Write a file | `Write` | `apply_patch` or shell heredoc | `write_file` | built-in write |
| Edit a file in place | `Edit` | `apply_patch` | `replace` | built-in edit |
| Search files by content | `Grep` | `shell` (rg/grep) | `search_file_content` | built-in grep |
| Glob for paths | `Glob` | `shell` (find/ls) | `glob` | built-in glob |
| Fetch a URL | `WebFetch` | `shell` (curl) | `web_fetch` | built-in fetch |
| Web search | `WebSearch` | `shell` (curl + API) | `google_web_search` | built-in search |

## Frontmatter compatibility

The `allowed-tools` frontmatter field is **only consumed by Claude Code**. Other platforms ignore it harmlessly. You don't need to remove it when shipping to Codex / Gemini / OpenCode — it just becomes inert metadata.

If your platform has its own allow-list mechanism, refer to its docs. Generally the skill needs permission to:

- Execute shell commands matching `conductor *`, `npm install *`, `pandoc *`, `marp *`, `curl *`, and the project's `./scripts/*` paths
- Read and write files under `.gtm/runs/` and `gtm-output/`
- Make outbound HTTPS requests (workflow runs trigger Conductor web search; the skill itself doesn't, but `WebFetch` may be used to pull user-supplied URLs)

## Skill-discovery paths (where each platform looks)

The `gtm-mavericks` npm package's postinstall symlinks the skill into the right directory for every platform it detects:

| Platform | Where it looks for skills |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Claude Code (plugin marketplace) | `~/.claude/plugins/` |
| OpenAI Codex CLI | `~/.codex/skills/` |
| Gemini CLI | `~/.gemini/skills/` (or as a Gemini Extension — see below) |
| OpenCode | `~/.config/opencode/skills/` |

## Gemini CLI specifics

Gemini CLI activates skills through an `activate_skill` tool rather than auto-loading every skill on session start. If your Gemini setup doesn't pick up the skill from `~/.gemini/skills/` directly, an alternative is to publish it as a Gemini Extension with a `gemini-extension.json` manifest pointing at this directory. The SKILL.md content remains the same.

## OpenAI Codex CLI specifics

Codex CLI's skill system is more lightweight than Claude Code's. You may find that Codex picks up SKILL.md files placed at `~/.codex/skills/<name>/` automatically; otherwise refer to it from your `~/.codex/AGENTS.md` instructions ("when the user wants GTM strategy, consult `~/.codex/skills/gtm-mavericks/SKILL.md`").

## OpenCode specifics

OpenCode (sst/opencode) uses an XDG-style config tree. The skill is symlinked into `~/.config/opencode/skills/gtm-mavericks/`. Refer to it from your opencode config or AGENTS.md.

## Quick test — does my agent see the skill?

Open a fresh session on any agent and ask:

> "what skills do you have available? list them by name."

If `gtm-mavericks` appears, you're set. If not, check:

1. The symlink at the path above resolves: `ls -la ~/.claude/skills/gtm-mavericks/` (substitute your platform's path)
2. The SKILL.md is readable: `cat <path-above>/SKILL.md | head -10`
3. Your agent's skill discovery is enabled (check its docs)

## Reporting platform issues

If you hit a tool-name or path mismatch on Codex / Gemini / OpenCode that's not covered here, file an issue at [conductoross/awesome-skills](https://github.com/conductoross/awesome-skills/issues) with the platform name and the failing operation. We'll add it to this table.
