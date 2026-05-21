# awesome-skills

## Agent skills that don't end when your terminal does.

Most "agent skills" are markdown files your coding agent reads, then forgets. They run in your terminal, last as long as the session lasts, and die when you close the tab. Useful for snippets — useless for real work.

This repo collects skills of a different kind: **conversational front-ends to long-running [Conductor](https://orkes.io/content/) workflows**. The skill is what your agent talks to. The workflow is what actually does the work — on a server, for 30 to 60 minutes, in parallel across many LLM calls, with durable state that survives your session, your laptop closing, and you walking away for the weekend.

You ask your agent to run a task. The skill handles intake, launches the workflow, and then your agent translates state into plain English on demand. You come back hours later, ask "where are we?", and pick up exactly where you left off.

```bash
npx @conductor-skills/gtm    # installs the flagship skill into every agent we detect
```

## Why skills + workflows

A skill alone is a prompt. Helpful for one-shot tasks, but it owns no state, can't run in parallel, can't run while you're away, and can't be audited after the fact.

A skill backed by a [Conductor](https://github.com/conductor-oss/conductor) workflow gets you:

- **Durability.** Workflow state lives on the server. Close your laptop. Switch agents. Restart your machine. Come back tomorrow and resume.
- **Real parallelism.** Six LLMs critique the same artifact at once, then a judge composes the winner. Not chained prompts — actual parallel forks with structured outputs.
- **Iterative refinement loops.** Draft → adversarial probe → revised draft, repeated until a quality gate is satisfied. Hard to do in a single prompt; trivial in a workflow.
- **Audit trail.** Every artifact traces back to the panel critique, judge decision, or strategic fork that produced it. No "the model just said so."
- **Mid-run inspection.** Ask "show me the ICP" while the workflow is on phase 4 — the skill surfaces whatever the synthesis loop has produced so far. Ask to "pause" and the run actually halts.
- **Concurrent runs.** Multiple workflows in flight at once, disambiguated by name. The skill keeps them straight.

The skill is the interface humans want. The workflow is the engine the work actually needs. Together you get something most "agentic" demos can't deliver: tasks that take a long time, parallelize across many model calls, hold state across sessions, and produce auditable output.

This is the same engine running production AI agents at scale via [AgentSpan](https://orkes.io/) — packaged as skills you install into your coding agent in one command.

## What's here

| Skill | What it does | Status |
|---|---|---|
| [**gtm-mavericks**](gtm-mavericks/) | Runs your go-to-market through a debate panel of six marketing legends (Draper, Jobs, Ogilvy, Clow, Halbert, Dunford). Produces ICP, positioning, messaging house, sales playbook, landing/ad/outbound copy, and a PDF that preserves every strategic disagreement as an appendix. 30–60 minute durable run. | Shipped |

More skills are in the works. Each follows the same shape: a single `SKILL.md` that drives intake and status, a `references/workflow-definitions/` directory with one or more Conductor workflows, persona/prompt/output templates, and an evals suite that runs on every PR.

## Install

Each skill ships its own one-command installer.

```bash
# gtm-mavericks — installs into every coding agent we detect
npx @conductor-skills/gtm

# Just one agent
npx @conductor-skills/gtm --agent codex

# Also set up a local Conductor server and register workflows
npx @conductor-skills/gtm --bootstrap
```

The installer auto-detects which agents you have on the machine and symlinks the skill into each. `--bootstrap` is interactive and re-runnable: it offers to start a local OSS Conductor server (downloads the jar once, finds an open port), or accepts a URL you point at.

To remove: `npx @conductor-skills/gtm --uninstall`.

## Agent compatibility

| Agent | Skill path |
|---|---|
| **Claude Code** | `~/.claude/skills/<skill>/` |
| **Codex CLI** | `~/.codex/skills/<skill>/` |
| **Gemini CLI** | `~/.gemini/skills/<skill>/` |
| **OpenCode** | `~/.config/opencode/skills/<skill>/` |
| **Other agents** | Drop the directory anywhere your agent reads skills from |

The skill format — markdown plus YAML frontmatter — is portable. Tool-name conventions differ slightly across platforms (`Bash` on Claude becomes `run_shell_command` on Gemini, etc.); each skill ships a `references/platform-tools.md` mapping table.

## Anatomy of a skill in this repo

If you want to build your own, here's the shape every skill in this repo follows:

```
<skill-name>/
├── SKILL.md                          # Conversational orchestrator the agent loads
├── bin/                              # npx installer
├── docs/design/architecture.md       # Engineering reference
├── references/
│   ├── workflow-definitions/         # Conductor workflows (register via PUT /api/metadata/workflow)
│   ├── personas/                     # Structured persona contracts, if applicable
│   ├── prompt-templates/             # Per-phase prompts inlined into workflow JSON
│   ├── output-templates/             # Mustache-style markdown for each artifact
│   └── platform-tools.md             # Tool-name mapping per agent
├── scripts/
│   ├── install_check.sh              # Interactive deps + Conductor server setup
│   ├── register_workflows.sh         # Idempotent upsert of workflow definitions
│   └── build_workflow.py             # Canonical workflow patcher
├── evals/                            # Static + bundle + e2e tiers, runs on every PR
└── package.json                      # @conductor-skills/<name>
```

The principle: **the skill is conversational and stateless; the workflow is durable and parallel.** Anything that needs to survive a session belongs in the workflow. Anything the user types belongs in the skill.

Read [`gtm-mavericks/docs/design/architecture.md`](gtm-mavericks/docs/design/architecture.md) for a full worked example — mode routing, synthesis loops, three-voice judge, persona contracts, concurrency model, decision log.

## Contributing

PRs welcome. If you're building a skill that follows the pattern above — a conversational layer over a Conductor workflow that does work humans can't reasonably do in a single prompt — we want it in the repo.

Open an issue first if you're proposing a new skill, so we can align on scope. For changes to existing skills, run the static eval tier before pushing (`python3 <skill>/evals/runner.py --tier static`); the full bundle and e2e evals run automatically on PR.

Found a tool-name mismatch on a non-Claude agent? Open an issue — we'll add it to the relevant `platform-tools.md`.

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
