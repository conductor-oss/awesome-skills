# Changelog

All notable changes to gtm-mavericks. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project uses semver while pre-1.0.

## [0.2.1] — 2026-05-20

One-command install via npx, with per-agent targeting.

### Added
- **`bin/gtm.js`** — unified installer entry. Available as `npx @conductor-skills/gtm` (no global install needed). Flags:
  - `--agent <id>` — install only into one agent (`claude-code`, `codex`, `gemini`, `opencode`, `claude-code-plugins`). Comma-separated for multiple. `all` installs everywhere.
  - `--bootstrap` — additionally run `install_check.sh` (Conductor server setup) and `register_workflows.sh`.
  - `--bootstrap-only` — skip symlinking; only bootstrap Conductor.
  - `--uninstall` — remove every symlink.
  - `--help`, `--quiet`.
- New `bin.gtm` entry in `package.json` so `npx @conductor-skills/gtm` resolves to the unified installer.

### Changed
- `bin.gtm-install` and `bin.gtm-uninstall` now point at `bin/gtm.js` (basename detection sets the right flag). Behavior unchanged for users of the global `gtm-install` / `gtm-uninstall` commands.
- `bin/postinstall.js` now delegates to `bin/gtm.js`. **Skips itself under `npx` (`npm_command === 'exec'`)** so flags like `--agent codex` aren't pre-empted by an unconditional auto-symlink during the `npx` fetch phase.
- README installation section rewritten to lead with the one-command `npx` flow.

### Removed
- `bin/install.js` and `bin/uninstall.js` — folded into `bin/gtm.js`.

### Migration

No breaking changes for users. Existing `npm install -g @conductor-skills/gtm` continues to work and auto-symlinks. Existing `gtm-install` and `gtm-uninstall` commands continue to work.

## [0.2.0] — 2026-05-20

Substantive cleanup pass: removed several intake fields the workflow silently ignored, fixed misleading docs, added a full engineering design doc.

### Changed
- **Workflow `gtm_mavericks_v1.json`:**
  - `inputParameters` cleaned: added `llm_provider` + `llm_model` declaratively; removed `output_formats`, `notifications`, `persona_library_version` (were no-ops).
  - `normalize_intake` now validates `mode` against the three known values and fails terminally with `invalid_mode: ...` if invalid — matches the existing missing_product_* validation pattern.
  - All 39 `${workflow.input.llm_provider/llm_model}` references rewritten to `${normalize_intake.output.result.llm_*}`. This makes the default-fallback logic in `normalize_intake` actually apply when callers omit the field — previously, unset values resolved to the literal string `${workflow.input.llm_model}` and the Anthropic provider rejected the call with a confusing error.
  - SUB_WORKFLOW input parameters (the three `discovery_*_ref` tasks) now pass the resolved llm_provider/llm_model values.
  - Description cleaned (dropped internal sprint numbering).
- **Discovery sub-workflows** (`discovery_{new_product,reposition,campaign}.json`): added `llm_provider` + `llm_model` to inputParameters, wired through to the discovery LLM call so the chosen model applies to discovery too (previously hardcoded to claude-sonnet-4-5).
- **SKILL.md:**
  - Intake wizard slimmed from 10 to 7 questions (dropped Deliverables / Output formats / Notifications steps).
  - Added shorthand model normalization rules ("sonnet" → `claude-sonnet-4-6`, "opus" → `claude-opus-4-7`, etc.).
  - Added three-element vague-description check (what / who / unfair angle) on top of the 20-char floor.
  - Status translation section now has an explicit `taskReferenceName` → user-facing-phase mapping table.
  - "Gate handling" section reworked into "Reviewing artifacts": the workflow does not pause at gates; review is opportunistic; revision = fresh run; reject = `conductor workflow terminate`.
  - Asset voice section rewritten: every run generates 3 voices (Dunford/Halbert/Ogilvy) in parallel and a judge picks per asset. The user does not pick a voice at intake.
  - Error recovery section rewritten as 3 failure-class tables (intake validation, LLM/provider, infrastructure).
  - New "Concurrent runs" subsection — `.gtm/active-run` is now a most-recent pointer, not an exclusive lock.
  - `state.json` now stores `productName` for cross-run disambiguation.
  - Gotcha #6 (SUB_WORKFLOW output propagation) rewritten as resolved via `discovery_normalize`.
  - Cross-platform finalization (`open` / `xdg-open` / `start`, fallback to print path).
  - `/gtm review` command now has a concrete definition.
- **README.md:**
  - Removed misleading claims about user-picked voice, "pause for you in chat" gates, in-flight revision, and short-circuit modes.
  - "How it works" rewritten to reflect: unattended 30–60min runs; opportunistic review; explicit `pause` if halt is needed; 3-voice judge model for assets.
  - Reflected concurrent-runs support throughout.
  - Updated "Try it" examples to remove unsupported flows.
  - Philosophy bullet "One voice ships" → "Three voices per asset, judged."
- **Walkthroughs** (`examples/mode_{a,b,c}_walkthrough.md`): intake steps + asset voice sections updated to reflect the new intake fields and 3-voice judge model.

### Added
- **`docs/design/architecture.md`** — full engineering design doc (931 lines, 17 sections) covering system architecture, workflow internals (mode routing, synthesis loops, 3-voice judge, polyglot proxy workarounds), persona contract, concurrency model, test strategy, limitations, extension points, and decision log.
- Repo-root `.gitignore` entries for `.gtm/` and `gtm-output/` so per-user runtime data never lands in commits.

### Removed
- `output_formats`, `notifications`, `persona_library_version` from intake (were collected but ignored by the workflow).
- `deliverables` from intake (was collected but ignored; every run generates all 4 asset types).
- Stale workflow-version internal numbering ("v24") from the workflow description.

### Migration

Re-register workflows before next run:

```bash
./scripts/register_workflows.sh
```

If you have existing intake JSONs with `deliverables` / `output_formats` / `notifications` / `persona_library_version` fields, they will be ignored (no error). Strip them when you next touch the file.

The workflow version stays at `1`. Next run still uses `--version 1`.

## [0.1.1] — earlier

Initial public release.
