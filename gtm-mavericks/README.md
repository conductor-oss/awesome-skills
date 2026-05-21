# gtm-mavericks

## Six legendary marketers walk into a workflow. They argue. The disagreements are preserved.

gtm-mavericks is a skill for your coding agent that runs your go-to-market strategy through a debate panel of six marketing legends — Don Draper, Steve Jobs, David Ogilvy, Lee Clow, Gary Halbert, and April Dunford. They critique your ICP. They fight over positioning. Disagreements are preserved as strategic forks rather than smoothed away. The output is ship-ready: ICP, positioning, messaging house, sales playbook, landing copy, ad copy, outbound sequences — plus a PDF that preserves every strategic disagreement as an appendix.

Built for marketers tired of AI-generated GTM that all sounds the same.

[![CI](https://github.com/conductor-oss/awesome-skills/actions/workflows/gtm-mavericks-evals.yml/badge.svg?branch=main)](https://github.com/conductor-oss/awesome-skills/actions/workflows/gtm-mavericks-evals.yml)

## How it works

When you run the skill, you walk through a short intake — what's the product, who's the buyer if you know, what mode (launching new / repositioning / campaign). Then a [Conductor](https://orkes.io/content/) workflow takes over and runs for the next 30 to 60 minutes on a server, not in your terminal.

First, *discovery*. Anthropic's web_search tool browses the market for you and pulls customer signals from any corpus URLs or files you handed over. The output is real quotes with citable sources — not "imagine your customer thinking..."

Then the panel kicks in. Six personas, each in their own parallel LLM task, each instructed to apply *only* their operating principles and evaluation questions. Draper goes hard on emotion — *what does the buyer want to feel?* — and kills any line that could run unchanged for a competitor. Jobs reduces everything to one sentence and names the enemy. Ogilvy demands a proof point per claim. Clow asks whether anyone would actually share the work. Halbert wants the offer, the urgency, and the P.S. Dunford forces the panel through his five-component canvas: alternatives, attributes, value, customer, category.

A synthesis loop runs after each panel — draft, Socratic adversarial probe, revised draft, again — until the probe returns satisfied or hits the configured iteration cap. Disagreements that don't resolve become **strategic forks** in the output: concrete tradeoffs with real consequences (CAC payback, claim rate, AOV) rather than "more emotional vs. more rational."

The workflow runs end-to-end in 30–60 minutes without supervision. You can review artifacts opportunistically — ask "show me the ICP" mid-run and the skill surfaces whatever the synthesis loop has produced so far. If you actually want to halt for review, say "pause" and the skill calls `conductor workflow pause` so nothing advances until you resume. You never see workflow IDs or raw JSON; the skill translates state into plain English.

Asset generation runs all three voices in parallel — Dunford, Halbert, Ogilvy — for every asset, and a judge LLM picks the strongest variant per item. The bundle carries the judge's picks; the other variants stay in the appendix so you can compare. Then everything gets rendered to a 3-tier markdown + PDF inside Conductor — no local LaTeX, no pandoc.

You can walk away at any point. Conductor holds the state. Come back hours or days later and ask "where are we?" — the skill reads each `.gtm/runs/<run-id>/state.json`, queries Conductor, and translates the current task into plain English. Multiple concurrent runs are supported; disambiguate by product name ("status for FlightCalm").

**Why this works:** No human carries Draper, Jobs, Ogilvy, Clow, Halbert, *and* Dunford in their head simultaneously. A workflow can. The result is strategy with all six lenses applied — sharper than any single PMM's output, even a great one, because no individual avoids their own blind spots. The preserved strategic forks force the operator to make the real calls rather than smoothing them away.

## Installation

One command, no global install required:

```bash
# Install into every coding agent we detect (Claude Code, Codex, Gemini CLI, OpenCode)
npx @conductor-skills/gtm

# Or pick one
npx @conductor-skills/gtm --agent codex

# Add --bootstrap to also set up a local Conductor server and register workflows
npx @conductor-skills/gtm --bootstrap
```

That's it. The installer auto-detects which agents you have, symlinks the skill into each, and prints next steps. The `--bootstrap` flag is interactive — for the Conductor server, it offers to start one locally for you (downloads the OSS jar once, finds an available port if 8080 is taken) or accepts a URL you provide. Re-runnable; safe to retry.

Want it globally on your PATH? `npm install -g @conductor-skills/gtm` still works and runs the same auto-detect. After that, `gtm`, `gtm-install` (= `--bootstrap`), and `gtm-uninstall` are available directly.

To remove: `npx @conductor-skills/gtm --uninstall`.

Start a new session in your agent and try:

> let's run a gtm for a new product I have

If a marketer named Draper starts arguing with someone named Dunford about your ICP, you're good.

## The panel

Each persona is a structured operating system in `references/personas/<name>.md` — not a vibe-based costume.

| Persona | Signature move | Strongest at |
|---|---|---|
| **Don Draper** | "It's toasted." Reframes objections as virtues. Headlines before body. Refuses bullet lists. | B2C, lifestyle, category creation |
| **Steve Jobs** | Reduces to one sentence. Names the enemy. "1,000 songs in your pocket." | Premium, experience-led products |
| **David Ogilvy** | Long copy that earns the short version. Proof per claim. "The loudest noise is the electric clock." | B2B, considered purchases |
| **Lee Clow** | Cultural manifesto. Brand at the center, product at the edges. "Here's to the crazy ones." | Challenger brands |
| **Gary Halbert** | Offer plus urgency plus proof plus P.S. "Dear Friend..." Direct-response. | DTC, info products, outbound |
| **April Dunford** | Five-component canvas. Sales-narrative test. Names the actual alternative the buyer is considering. | B2B SaaS |

Each file has structured fields that define the persona contract: `operating_principles`, `evaluation_questions`, `signature_moves`, `anti_patterns`, `voice_samples`, `panel_contribution`. In the current v1 workflow, the task prompts embed distilled persona rules directly, so persona edits must be propagated into the workflow JSON before re-registering.

## A real disagreement

Excerpted verbatim from a workflow run on a craft chocolate subscription (Mode B reposition):

> **Strategic fork: First Purchase Offer — Single Bar vs. Tasting Flight**
>
> **Option A — $18 single bar with guarantee.** If you don't taste the difference from Dandelion in the first bite, keep the bar and we refund.
>
> > *Tradeoff: slower subscriber acquisition. Most buyers need 2–3 purchases before subscribing, extending CAC payback from 1 month to 3–4. Lower AOV means more transactions to break even. Guarantee claim rate is real risk at industry-typical 15–20%.*
>
> **Option B — $39 three-bar tasting flight with guarantee.** Three distinct origins with side-by-side tasting guide.
>
> > *Tradeoff: $39 feels steeper to ICPs who "don't want another $18 mistake" (now asking for a $39 mistake). Decision paralysis on origin selection. Guarantee exposure is 3x.*
>
> **Recommendation: Option A.**

This is what the panel produces when Draper, Halbert, and Dunford actually argue: concrete tradeoffs the operator can reason about, not synthesized-to-average mush. Full bundle at [`evals/bundle/fixtures/example.bundle.json`](evals/bundle/fixtures/example.bundle.json).

## Try it

Paste any of these into your agent. The intake wizard takes it from there, one question at a time.

**New product, no traction yet:**
> let's run gtm for FlightCalm — iOS app using Apple Watch HRV to trigger mid-flight breathing exercises for anxious flyers. 4 interview transcripts in ~/Desktop/interviews/.

**Repositioning a B2B SaaS that hit a plateau:**
> we sell Hublink. $8M ARR Series B. Win rate dropped 15% YoY against Linear/Notion. Demos land, deals stall. Reposition.

**Launch campaign with positioning already set:**
> Earnpay Advance — instant earned-wage access for hourly workers in 12 states. Positioning is already fixed and approved. Run the campaign mode.

**Mid-run check-in:**
> where are we on the gtm run?

**Halt for review:**
> pause the run, I want to look at the ICP before positioning starts

**Pause and resume across sessions:**
> pause the run, I'll be back tomorrow
>
> *(next day, fresh session)* — where were we?

**Compare voice variants from a finished run:**
> show me the Halbert variant of the landing copy — I want to compare it to what the judge picked

**Run something new with a sharper angle:**
> the positioning from yesterday's run is fine but I want to test a category-creation play. Start a fresh run with that frame.

## What you get

When a run completes, deliverables land in `gtm-output/<run-id>/`:

- **`gtm-full.md`** + **`gtm-full.pdf`** — the assembled 3-tier doc: Executive Summary → Part 1 Deliverables → Part 2 Appendix (panel disagreements and decisions log). PDF generated server-side, no local LaTeX needed.
- **`bundle.json`** — all artifacts as structured JSON for downstream tooling, including the non-winning voice variants for each asset.
- **`executive_summary.json`** — TL;DR, key decisions, 90-day action plan, KPIs, gaps and risks.
- **`gtm-deck.pdf`** / **`gtm-deck.html`** — only if you ask for them after the run. Slides are a separate post-run render via `scripts/render_slides.sh` (requires marp).

The PDF preserves the panel's disagreements as an appendix. Every line in the executive summary traces back through the decisions log to a recorded panel critique or strategic fork. Audit-friendly strategy.

## Agent compatibility

| Agent | Experience | Skill path |
|---|---|---|
| **Claude Code** | Full skill + intake wizard + opportunistic artifact review | `~/.claude/skills/gtm-mavericks/` |
| **Codex CLI** | Full skill | `~/.codex/skills/gtm-mavericks/` |
| **Gemini CLI** | Full skill | `~/.gemini/skills/gtm-mavericks/` |
| **OpenCode** | Full skill | `~/.config/opencode/skills/gtm-mavericks/` |
| **Other agents** | Manual: drop the directory anywhere your agent reads skills from | see [`references/platform-tools.md`](references/platform-tools.md) |

The skill file format (markdown + YAML frontmatter) is portable. Tool-name conventions differ slightly per platform (`Bash` on Claude becomes `run_shell_command` on Gemini, etc.) — the mapping table in `platform-tools.md` covers the differences. Override the auto-symlink with `GTM_INSTALL_TARGETS=claude-code,codex` (comma-separated) or `GTM_INSTALL_TARGETS=none`.

## What's inside

**Core skill** — [`SKILL.md`](SKILL.md) — conversational orchestrator. Runs intake, launches the workflow, translates status to plain English on request, surfaces in-progress artifacts when asked, pauses or terminates the run on the user's command, and renders final outputs at completion.

**Design doc** — [`docs/design/architecture.md`](docs/design/architecture.md) — engineering reference covering system architecture, workflow internals (mode routing, synthesis loops, 3-voice judge, polyglot proxy workarounds), persona contract, concurrency model, test strategy, limitations, and decision log. Read this before extending the workflow or debugging anything non-obvious.

**Workflow definitions** — `references/workflow-definitions/` — four Conductor workflows: a 25-task main workflow plus three mode-specific discovery sub-workflows. All ship ready to register via `PUT /api/metadata/workflow`.

**Personas** — `references/personas/` — six maverick files with structured fields. Plain markdown, hand-editable. They are the editing contract for the persona library; the current workflow JSON embeds distilled persona rules in task prompts.

**Prompt templates** — `references/prompt-templates/` — per-phase prompts inlined directly into workflow JSON task messages, so there's no external prompt registry to manage.

**Output templates** — `references/output-templates/` — Mustache-style markdown templates for each artifact type plus the full 3-tier doc and Marp slide deck.

**Eval suite** — `evals/` — three tiers: static (33 checks, no API), bundle (schemas + 14 structural rules + 4 LLM-as-judge rubrics — ICP specificity, positioning differentiation, persona voice, anti-messaging), e2e (full Conductor run + grade). Runs on every push and PR.

**Bootstrap scripts** — `scripts/install_check.sh` (interactive deps and Conductor server setup), `scripts/register_workflows.sh` (idempotent PUT-array upsert), `scripts/build_workflow.py` (canonical workflow patcher).

## Philosophy

- **Disagreement > consensus.** Six perspectives that argue produce sharper strategy than one that smooths to averages.
- **Personas as operating systems.** Encoded as structured fields the workflow applies mechanically, not vibes.
- **Operator decides.** Strategic forks are preserved as choices, never auto-resolved.
- **Three voices per asset, judged.** Every asset is drafted in three voices in parallel and a judge LLM composes the strongest. The losing variants stay in the bundle for comparison rather than being thrown away.
- **Audit-friendly.** Every line of output traces back to a panel critique or a recorded decision.
- **Substance over style.** The maverick framing only works because the underlying GTM rigor is real.

## Customization

**Edit a persona.** Open the markdown file at `references/personas/<name>.md`. Change `signature_moves`, sharpen `anti_patterns`, add `voice_samples`, then propagate those changes into the matching prompts in `references/workflow-definitions/gtm_mavericks_v1.json` and re-register workflows. The current v1 workflow does not read persona markdown files dynamically at runtime.

**Add a 7th persona.** Drop a file at `references/personas/<name>.md` matching `draper.md`'s schema. Add the new persona to both the `icp_panel` and `positioning_panel` forks in `references/workflow-definitions/gtm_mavericks_v1.json`. Re-register with `./scripts/register_workflows.sh`.

**Output templates.** Mustache-style `{{double-brace}}` in `references/output-templates/`. Tweak headers, ordering, branding.

## Troubleshooting

Most setup issues are caught by `install_check.sh` with actionable next steps. The common ones:

- **"Java 21 required"** when starting the local Conductor server → `brew install openjdk@21` on macOS, `sudo apt install openjdk-21-jdk` on Linux.
- **Port 8080 busy** → `install_check.sh` auto-falls-back to 8081 / 8090 / 9080 / 18080 / 28080.
- **`register_workflows.sh` returns 401** → your server requires auth. Set `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` (Orkes Cloud) before re-running.
- **Workflow registration fails with "task type LLM_CHAT_COMPLETE not supported"** → you're on OSS Conductor without the AI plugin. Switch to Orkes Conductor or replace the `LLM_CHAT_COMPLETE` tasks with `SIMPLE` tasks fronted by a custom worker.
- **Agent doesn't see the skill** → confirm the symlink (`ls -la ~/.claude/skills/gtm-mavericks/SKILL.md`), restart the agent.
- **"No route to host" errors mid-run** → JVM DNS cache went stale after a transient network outage. `conductor server stop && conductor server start` to flush.

## Contributing

PRs welcome at [`conductor-oss/awesome-skills`](https://github.com/conductor-oss/awesome-skills). Run `python3 evals/runner.py --tier static` before pushing. The full bundle evals (with LLM judges) run automatically on PR. Found a tool-name mismatch on a non-Claude agent? Open an issue — we'll add it to `references/platform-tools.md`.

## License

Apache-2.0 — see [`LICENSE`](../LICENSE) at the repo root.
