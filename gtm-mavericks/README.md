# gtm-mavericks

## Six legendary marketers walk into a workflow. They argue. The disagreements are preserved.

A Claude Code skill that runs your go-to-market through a debate panel of **Don Draper, Steve Jobs, David Ogilvy, Lee Clow, Gary Halbert, and April Dunford** — each encoded as a structured operating system, not a costume. They critique your ICP, fight over positioning, and only commit to one voice when *you* say so. The output: ship-ready ICP, positioning, messaging house, and asset copy — with every strategic fork preserved as a real choice for the operator.

**Built for marketers tired of AI-generated GTM that all sounds the same.**

Runs on [Conductor](https://orkes.io/content/) (OSS or Orkes Cloud). Long-running (~30–60 min). Resumes conversationally across sessions. Cross-platform: Claude Code, Codex CLI, Gemini CLI, OpenCode.

[![CI](https://github.com/conductor-oss/awesome-skills/actions/workflows/gtm-mavericks-evals.yml/badge.svg?branch=main)](https://github.com/conductor-oss/awesome-skills/actions/workflows/gtm-mavericks-evals.yml)

---

## The panel

Each persona is a YAML-fronted markdown file at `references/personas/<name>.md` with structured fields: `operating_principles`, `evaluation_questions`, `signature_moves`, `anti_patterns`, `voice_samples`, `panel_contribution`. The workflow LLM tasks reference these fields directly — not "act like Don Draper" prompts, but specific operating-system invocations.

| Persona | Worldview | Strongest at |
|---|---|---|
| **Don Draper** | Emotional truth. *"Advertising is happiness."* Kills positioning that doesn't make you *feel*. | B2C, lifestyle, category creation |
| **Steve Jobs** | Reduction. Names the enemy. *"1,000 songs in your pocket."* | Premium / experience-led products |
| **David Ogilvy** | Proof. Long-copy. Specifics. *"The loudest noise is the electric clock."* | B2B, considered purchases |
| **Lee Clow** | Cultural manifesto. Challenger frame. *"Here's to the crazy ones."* | Challenger brands |
| **Gary Halbert** | Direct response. Offer. Urgency. *"The most powerful force is a starving crowd."* | DTC, info products, outbound |
| **April Dunford** | Operational rigor. Five-component canvas. Sales-narrative test. | B2B SaaS |

Together they have ~250 years of combined marketing experience. The skill puts them in a panel that no working marketer could otherwise assemble.

---

## A real disagreement

Excerpted verbatim from a real workflow run (a craft chocolate subscription — Mode B reposition):

> **Strategic fork: First Purchase Offer — Single Bar vs. Tasting Flight**
>
> **Option A — Trust-First Single Bar.** One $18 bar with unconditional satisfaction guarantee. If you don't taste the difference from Dandelion in the first bite, keep the bar and we refund you.
>
> > **Tradeoff:** *Slower subscriber acquisition — most buyers need 2-3 individual purchases before subscribing, extending CAC payback from 1 month to 3-4 months. Lower AOV ($18 vs $39) means more transactions needed to reach breakeven. Guarantee claim rate risk if 15-20% of first-time buyers claim it.*
>
> **Option B — Trust-First Tasting Flight.** Three-bar curated flight at $39 featuring three distinct origins with side-by-side tasting guide.
>
> > **Tradeoff:** *Higher friction at first purchase — $39 commitment vs $18 feels steeper when trust hasn't been earned yet, particularly for ICPs who "don't want another $18 mistake" (now asking for a $39 mistake). Decision paralysis on "which three origins?" if buyer has to choose. Guarantee exposure is 3x.*
>
> **Recommendation: Option A.**

That's the kind of fork a panel produces when Draper, Halbert, and Dunford argue — concrete consequences (CAC payback, claim rate, AOV) rather than "more emotional vs. more rational." Operators can actually pick.

Full bundle is at [`evals/bundle/fixtures/example.bundle.json`](evals/bundle/fixtures/example.bundle.json) — including ICP, positioning, messaging house, and the panel's preserved disagreements.

---

## Try it — paste any of these into Claude

The skill runs an intake wizard from any of these prompts. One question at a time, conversationally.

### New product, no traction yet (Mode A)

> Let's run a gtm for a new product. I'm building **FlightCalm** — an iOS app that uses Apple Watch heart-rate variability to trigger personalized breathing exercises mid-flight for people with flight anxiety. No traction yet. I have 4 interview transcripts in `~/Desktop/flightcalm/interviews/` and a one-pager concept doc.

→ Mode A: discovery with corpus + web search, full 6-persona panel debate on ICP and positioning, messaging house, asset voice gate, deliverables.

### Repositioning a B2B SaaS that hit a plateau (Mode B)

> We sell **Hublink** — async-first team workspace. $8M ARR, Series B. Win rate dropped 15% YoY against Linear/Notion. Demos land but deals stall. We need to reposition. I'm uploading lost-deal transcripts and current website copy. Run a full repositioning.

→ Mode B: discovery focused on lost-deal patterns + current-positioning audit, panel argues about who the *real* buyer is now, "broaden vs. narrow the category" forks, messaging house with explicit anti-messaging, assets in Dunford's voice.

### Launch campaign with positioning already set (Mode C)

> Launch campaign for **Earnpay Advance** — instant earned-wage access for hourly workers, just approved in 12 states. Positioning is set: "Cash you've earned, before payday — no fees, no credit check, no debt." Buyers are 22-38 hourly workers earning $15-25/hr at retail/food service. I need messaging house, landing copy, ad copy variants, and a 4-email outbound sequence in Halbert's direct-response voice.

→ Mode C: skips the long debates, focuses discovery on channels + trigger events, generates campaign-ready assets in the requested voice (~10-15 min instead of 30-60).

### Mid-run check-in

> Where are we on the GTM run?

→ Plain-English status: "*40% through, 12 min in, the panel is debating positioning; want to see the ICP draft?*"

### Force a specific persona voice on assets

> When you get to the asset voice pick, use Draper — the emotional-truth one. I want headlines, not bullet lists.

→ Commits Draper at the voice gate. Outbound, ad copy, and landing copy all carry his signature moves.

### Pause and resume

> Pause the run. I'll come back to it tomorrow.
>
> *(next day, fresh session)*
>
> Where were we on the GTM run?

→ `conductor workflow pause` / `resume`. Skill picks up the active run from `.gtm/active-run` and surfaces any pending gate.

### Iterate on positioning without re-running everything

> The positioning we just landed is good but I want to test a category-creation play instead. Re-run positioning with that frame.

→ Terminates the current run, starts a new one with the framing, resurfaces positioning for review.

### Short-circuit a fast run

> Give me messaging house + landing copy + 3 ad copy variants for **<product>**, voice: Dunford. Skip the long synthesis loops.

→ Mode C with `max_synthesis_iterations: 1`, narrowed deliverables, ~10-15 min total.

---

## Install

```bash
npm install -g @conductor-skills/gtm
gtm-install
```

The postinstall auto-symlinks the skill into every agent platform it detects on your machine (Claude Code, Codex, Gemini CLI, OpenCode). Then `gtm-install` is the interactive bootstrap — it offers you a choice:

```
This skill needs a Conductor server. Choose:
  1) I have a server — I'll provide the URL
  2) Start a local one for me (downloads ~600MB on first run)
  3) Skip for now
```

Pick **2** if you don't have Conductor running. The script checks if port 8080 is free, falls back to 8081 / 8090 / 9080 / 18080 / 28080 if not, downloads the OSS jar, boots the server, and tells you exactly what to `export` to make it permanent.

After setup, open Claude Code in any project and try one of the [example prompts](#try-it--paste-any-of-these-into-claude) above.

---

## How it works

```
intake → discovery → ICP panel → positioning panel → messaging house → asset voice → assets → bundle + PDF
   ↓        4–8m       3–10m          3–10m              3–10m         pick one     4–8m         seconds
              ↑              ↑               ↑                              ↑              ↑
       conversational   conversational  conversational              conversational  conversational
            gate           gate            gate                          gate            gate
```

| Phase | Mechanism |
|---|---|
| **Intake** | Conversational wizard. Mode (A/B/C), product, ICP hypothesis, corpus, deliverables, output formats. |
| **Discovery** | `LLM_CHAT_COMPLETE` with `webSearch: true` (Anthropic's native web_search tool) does multi-turn research itself. Returns customer signals with citable URLs. Pulls from user-supplied corpus too. |
| **ICP / Positioning panels** | `FORK_JOIN` of 6 persona critique tasks in parallel, each instructed to apply only that persona's `operating_principles` and `evaluation_questions`. |
| **Synthesis loops** | `DO_WHILE` per panel: draft → Socratic adversarial probe → revised draft. Up to N iterations (configurable per run). Probes that recur unresolved across 3 iterations move to `documented_gaps`. |
| **Messaging house** | Dunford-led operational chassis. Category, north star, audience promise, proof pillars (each tied to evidence), taglines (mix of voices), anti-messaging. |
| **Asset voice pick** | The single most important operator decision. The panel produced material; one voice owns the assets. |
| **Asset generation** | `FORK_JOIN_DYNAMIC` over selected deliverables. 3 voice variants per asset (Dunford / Halbert / Ogilvy by default) + a judge LLM that picks per-item bests. |
| **Bundle + PDF** | Deterministic `INLINE` merge → executive summary LLM → markdown render → ASCII sanitize → `GENERATE_PDF` task (PDF generated inside Conductor, no local pandoc needed). |

**Conversational gates** — there are no blocking HUMAN tasks in the workflow. The skill surfaces each artifact at the phase boundary as a chat checkpoint, you respond approve / revise / reject, the conversation moves on while the workflow keeps running.

**Walk-away resumable** — Conductor holds workflow state. You can close Claude Code mid-run, come back hours later, and ask "where are we?" The skill reads `.gtm/active-run`, queries Conductor, summarizes in plain English.

For the full architecture (workflow JSON, prompt templates, schema contracts, known gotchas) see [`SKILL.md`](SKILL.md).

---

## What you get

When a run completes, deliverables land in `gtm-output/<run-id>/`:

| File | What it is |
|---|---|
| `gtm-full.md` | The assembled 3-tier doc: Executive Summary → Part 1 Deliverables → Part 2 Appendix (panel disagreements + decisions log) |
| `gtm-full.pdf` | Rendered by Conductor's `GENERATE_PDF` task — no local LaTeX or pandoc required |
| `bundle.json` | All artifacts as structured JSON, downstream-tooling-friendly |
| `executive_summary.json` | TL;DR, key decisions, 90-day action plan, KPIs, gaps & risks |
| `gtm-deck.pdf` / `gtm-deck.html` | If Marp is installed and slides were requested |

Bundle structure (per `references/artifact-schemas/*.schema.json`):

- `icp_one_pager` — primary ICP (demographic, psychographic, trigger event, current alternative, pain in their words), secondary candidates, rejected candidates, panel disagreements
- `positioning` — recommended positioning (Dunford five-component statement), strategic forks with tradeoffs, category design
- `messaging_house` — category, north star, audience promise, proof pillars (each tied to evidence), taglines (mix of voices), anti-messaging
- `artifacts[]` — one entry per deliverable type (sales playbook, landing copy, ad copy, outbound sequences, 90-day plan), each with `voice_persona` recorded

---

## Prerequisites & setup details

### Required (auto-installed by `gtm-install` when you confirm)

| Dependency | Why | Install |
|---|---|---|
| Node.js + npm | The Conductor CLI is npm-distributed | macOS: `brew install node` · Linux: `nodesource` |
| Conductor CLI | Talks to the server: `workflow create/start`, `task signal`, etc. | `npm install -g @conductor-oss/conductor-cli` |
| Conductor server | Where the workflow actually runs | Three choices in `gtm-install`: existing URL / local OSS / skip |
| Python 3 | JSON validation in `install_check.sh`, output rendering | Pre-installed on macOS; `apt-get install python3` on Linux |

### Optional (warn-only, gracefully skipped)

| Dependency | Why | Install |
|---|---|---|
| pandoc + PDF engine | Re-rendering markdown locally with custom styling. The workflow's primary PDF is generated server-side. | `brew install pandoc` + `brew install --cask basictex` (xelatex) or `pip install weasyprint` |
| Marp CLI | Slide-deck output | `npm install -g @marp-team/marp-cli` |

### Orkes Cloud (authenticated remote servers)

Set the auth env vars before `gtm-install`:

```bash
export CONDUCTOR_SERVER_URL="https://<your-cluster>.orkesconductor.io/api"
export CONDUCTOR_AUTH_KEY="<your-key-id>"
export CONDUCTOR_AUTH_SECRET="<your-key-secret>"
gtm-install
```

OSS Conductor (local or self-hosted) needs no auth.

### Manual install (from source, no npm)

```bash
git clone https://github.com/conductor-oss/awesome-skills.git
cd awesome-skills/gtm-mavericks

# Interactive bootstrap (deps + server)
./scripts/install_check.sh

# Register all 4 workflow defs
./scripts/register_workflows.sh

# Link into Claude Code (or your agent's skills dir)
ln -s "$(pwd)" ~/.claude/skills/gtm-mavericks
```

`install_check.sh` flags:

- (default) interactive — prompts before each install/setup action
- `--non-interactive` — check only, never install (CI mode)
- `--auto-install` — install everything possible, including starting a local Conductor server, without prompting

### Cross-platform install paths

When you `npm install -g @conductor-skills/gtm`, the postinstall symlinks the skill into every detected agent's directory:

| Platform | Skill path |
|---|---|
| Claude Code | `~/.claude/skills/gtm-mavericks/` |
| Claude Code (plugins / marketplace) | `~/.claude/plugins/gtm-mavericks/` |
| OpenAI Codex CLI | `~/.codex/skills/gtm-mavericks/` |
| Gemini CLI | `~/.gemini/skills/gtm-mavericks/` |
| OpenCode | `~/.config/opencode/skills/gtm-mavericks/` |

Override with `GTM_INSTALL_TARGETS=claude-code,codex` (comma-separated IDs) or `GTM_INSTALL_TARGETS=none` to skip auto-install entirely.

See [`references/platform-tools.md`](references/platform-tools.md) for tool-name mappings across platforms (`Bash` → `run_shell_command` for Gemini, etc.).

### Verify the skill is discoverable

In a fresh agent session:

```
list the marketing personas in gtm-mavericks
```

The agent should respond with the six personas and their `panel_role` from the persona files. If not, check the symlink (`ls -la ~/.claude/skills/gtm-mavericks/SKILL.md`) and restart the agent.

---

## Customization

### Editing personas

All persona definitions are plain markdown in `references/personas/`. Edit any of them — operating principles, evaluation questions, signature moves, anti-patterns, voice samples, panel contribution. Changes apply to the *next* run, not in-flight ones (personas are sealed into workflow input at start).

### Adding a 7th persona

1. Create `references/personas/<name>.md` following the same schema as `draper.md`.
2. Add the new persona to both `icp_panel` and `positioning_panel` `FORK_JOIN` lists in `references/workflow-definitions/gtm_mavericks_v1.json`.
3. Re-register: `./scripts/register_workflows.sh`.

### Output templates

Markdown with `{{double-brace}}` placeholders, in `references/output-templates/`. Tweak headers, ordering, branding as needed.

### Workflow customization

The main workflow is `references/workflow-definitions/gtm_mavericks_v1.json`. Use `scripts/build_workflow.py` (idempotent patcher) to apply known-correct fixes; bump the workflow version field before changes to keep Conductor's metadata cache honest.

---

## Evals & CI

The repo ships with a three-tier eval suite at `evals/`:

| Tier | What it checks | Cost / time |
|---|---|---|
| **Static** | Persona schemas, workflow JSON validity, prompt files present, frontmatter correct | ~1 sec, $0 |
| **Bundle** | Schema validation per artifact + 14 structural rules + 4 LLM-as-judge rubrics (`icp_specificity`, `positioning_differentiation`, `persona_voice`, `anti_messaging`) | ~60 sec + ~$0.10 |
| **E2E** | Spin up Conductor, run a full scenario, grade the output | 30-60 min + ~$5 per run |

GitHub Actions runs static + smoke (real Conductor boot + workflow registration) + bundle (LLM judges run if `ANTHROPIC_API_KEY` secret is configured, deterministic-only otherwise) on every push and PR.

```bash
# Run locally:
python3 evals/runner.py --tier static
python3 evals/runner.py --tier bundle --bundle evals/bundle/fixtures/example.bundle.json --judge-samples 3
./evals/e2e/run_e2e.sh evals/e2e/scenarios/mode_b_b2b_reposition.yaml
```

---

## Troubleshooting

**`install_check.sh` says `conductor CLI not found`**
The script will prompt to install it. If you decline or it fails, run: `npm install -g @conductor-oss/conductor-cli`. Requires Node.js (`brew install node` on macOS).

**Conductor server fails to start with "Java 21 required"**
The OSS Conductor server needs Java 21+. Install: `brew install openjdk@21` (macOS) or `sudo apt install openjdk-21-jdk` (Linux). Ubuntu's default `setup-java@v4` in CI workflows is `temurin/21`.

**Port 8080 is busy**
`install_check.sh` detects this and falls back to 8081 / 8090 / 9080 / 18080 / 28080 automatically. The export command it prints will reflect the actual port used.

**`register_workflows.sh` errors with 401**
Your Conductor server requires auth. Set `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` (Orkes Cloud key/secret pair), or set `CONDUCTOR_PROFILE` to a saved CLI profile.

**Claude Code doesn't see the skill**
- Confirm the symlink: `ls -la ~/.claude/skills/gtm-mavericks/SKILL.md`
- Restart Claude Code
- Check `/skills` in a Claude Code session

**Workflow registration fails with "task type LLM_TEXT_COMPLETE not supported"**
You're running OSS Conductor without the AI/LLM task plugin. Either switch to Orkes Cloud/self-hosted (built-in LLM tasks) or replace `LLM_CHAT_COMPLETE` tasks in the workflow with `SIMPLE` tasks fronted by a custom worker that calls Claude / OpenAI APIs.

**"No route to host" errors mid-run**
JVM DNS cache went stale after a transient network outage. Restart Conductor (`conductor server stop && conductor server start`) to flush. Alternatively, set the JVM flag `-Dsun.net.inetaddr.ttl=30` so the cache expires every 30 seconds.

**PDF output is missing**
The workflow's primary PDF is generated server-side by Conductor's `GENERATE_PDF` task (no local deps needed). If you want a *local* re-render with custom styling, install `pandoc` and a PDF engine (`brew install --cask basictex` for xelatex on macOS, `pip install weasyprint` as fallback).

**Persona voice doesn't sound distinctive enough**
Open the persona file (`references/personas/<name>.md`) and add to `signature_moves`, `anti_patterns`, and `voice_samples`. The more concrete and opinionated the persona definition, the more distinct the asset output. Then re-run.

---

## Project structure

```
gtm-mavericks/
├── README.md                                  ← you are here
├── SKILL.md                                   ← agent-loadable skill definition
├── plugin.json                                ← Claude marketplace metadata
├── package.json                               ← npm packaging (bin: gtm-install, gtm-uninstall)
├── bin/                                       ← postinstall + install/uninstall CLIs
├── references/
│   ├── personas/                              ← 6 marketing maverick persona files
│   ├── workflow-definitions/                  ← 4 Conductor workflow JSONs
│   ├── artifact-schemas/                      ← 8 JSON schemas for output validation
│   ├── prompt-templates/                      ← LLM prompts for each workflow phase
│   ├── output-templates/                      ← markdown templates for rendered deliverables
│   └── platform-tools.md                      ← cross-agent tool-name mapping
├── scripts/
│   ├── install_check.sh                       ← interactive deps + Conductor server setup
│   ├── register_workflows.sh                  ← PUT-array upsert of all 4 workflow defs
│   ├── build_workflow.py                      ← idempotent workflow patcher
│   ├── render_outputs.sh / .py                ← post-run output rendering
│   ├── render_pdf.sh                          ← optional pandoc PDF re-render
│   └── render_slides.sh                       ← optional Marp slides
├── evals/                                     ← three-tier eval suite (static / bundle / e2e)
└── examples/                                  ← walkthrough docs per mode (A/B/C)
```

---

## License

Apache License 2.0 — see [`LICENSE`](../LICENSE) at the repo root.

---

## Contributing

Pull requests welcome at [`conductor-oss/awesome-skills`](https://github.com/conductor-oss/awesome-skills). Run `python3 evals/runner.py --tier static` before pushing. The full bundle evals (with LLM judges) run automatically on PR.

Found a tool-name mismatch on Codex, Gemini, or OpenCode? [Open an issue](https://github.com/conductor-oss/awesome-skills/issues) — we'll add it to `references/platform-tools.md`.

---

Made by [Orkes](https://orkes.io). Inspired by the proposition that no single human carries Draper, Jobs, Ogilvy, Clow, Halbert, and Dunford in their head — but a workflow can.
