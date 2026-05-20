# gtm-mavericks

A Claude Code skill that runs deep, multi-phase go-to-market strategy through a Conductor workflow, with a panel of six marketing-maverick personas — **Don Draper, Steve Jobs, David Ogilvy, Lee Clow, Gary Halbert, April Dunford** — who debate ICP and positioning, then commit one voice to your asset generation.

Designed for non-technical operators (PMM, founder, marketing lead). Long-running (30–60 min), resumes conversationally across sessions, never surfaces workflow IDs or JSON.

---

## What it does

Given a product, the workflow runs five phases:

1. **Discovery** — research the market, category, competitors, and pull customer signals from your corpus.
2. **ICP panel** — all 6 personas critique and propose ICP framings in parallel. Synthesis surfaces real disagreements as forks for you to resolve.
3. **Positioning panel** — same 6 personas, this time on positioning. Surfaces strategic forks (emotional vs operational, category-creation vs incumbent, brand vs direct-response).
4. **Messaging house** — built on Dunford's operational chassis.
5. **Assets** — you pick *one* persona to own the voice; the workflow generates your selected deliverables (sales playbook, landing copy, ad copy, outbound sequences, etc.).

Four conversational checkpoints surface for your review/approval: ICP, positioning, asset-voice pick, final review. The workflow runs autonomously on the Conductor server end-to-end (~30–60 min); Claude surfaces each checkpoint in chat at the phase boundary and collects your approval there. You can walk away between checkpoints.

Output: markdown + PDF (rendered inside Conductor) + optional slide deck (via Marp). Pick any subset at intake.

---

## Prerequisites

### Required

- **Node.js + npm** (for the Conductor CLI)
- **Conductor server** running and reachable. Options:
  - **Local OSS:** see [Conductor OSS quickstart](https://orkes.io/content/get-orkes-conductor#run-it-locally) — typically runs at `http://localhost:8080/api`
  - **Orkes Cloud:** sign in at [orkes.io](https://orkes.io) and use your cluster URL
- **`conductor` CLI:**
  ```bash
  npm install -g @conductor-oss/conductor-cli
  conductor --version
  ```
- **Python 3** (used by `install_check.sh` and `register_workflows.sh` for JSON validation)
- **Claude Code** — the skill runs as a Claude Code skill

### Optional (recommended)

- **pandoc** — PDF output. macOS: `brew install pandoc`. Debian/Ubuntu: `sudo apt-get install pandoc`. Also needs a PDF engine (`brew install --cask basictex` for `xelatex`, or `pip install weasyprint`).
- **Marp CLI** — slide-deck output. `npm install -g @marp-team/marp-cli`

The skill degrades gracefully without pandoc/Marp — you still get full markdown output, with a warning that PDF/slides were skipped.

---

## Install

### Quick install (recommended)

```bash
npm install -g @conductor-skills/gtm
```

That's it. The postinstall auto-detects every supported agent platform on your machine and symlinks the skill into each one's skills directory. Open whichever agent you use and the skill is available.

**Supported platforms** (auto-detected):

| Platform | Skill path |
|---|---|
| Claude Code | `~/.claude/skills/gtm-mavericks/` |
| Claude Code (plugins / marketplace) | `~/.claude/plugins/gtm-mavericks/` |
| OpenAI Codex CLI | `~/.codex/skills/gtm-mavericks/` |
| Gemini CLI | `~/.gemini/skills/gtm-mavericks/` |
| OpenCode | `~/.config/opencode/skills/gtm-mavericks/` |

Detection rule: a platform's parent config directory (`~/.claude/`, `~/.codex/`, etc.) must already exist. If it doesn't, the postinstall skips that platform — it never creates a config dir for a platform you haven't installed.

**Override detection** with the `GTM_INSTALL_TARGETS` env var:

```bash
# Install only to Claude Code, no matter what else is detected:
GTM_INSTALL_TARGETS=claude-code npm install -g @conductor-skills/gtm

# Install everywhere, even on platforms that aren't yet set up:
GTM_INSTALL_TARGETS=all npm install -g @conductor-skills/gtm

# Skip auto-install entirely (you'll link the skill manually):
GTM_INSTALL_TARGETS=none npm install -g @conductor-skills/gtm
```

Valid IDs: `claude-code`, `claude-code-plugins`, `codex`, `gemini`, `opencode` (comma-separated for multiple).

**Note on compatibility:** the skill file format (markdown with YAML frontmatter) is largely portable across these agents, but tool-name conventions differ slightly between platforms (Claude Code's `Bash` vs Codex's equivalents, for example). The `allowed-tools` line in `SKILL.md` is written for Claude Code; on other platforms most tool calls still work but some may need light adaptation. File issues at [`conductoross/awesome-skills`](https://github.com/conductoross/awesome-skills) if you hit a tool-name mismatch.

To finish setup, run the bootstrap. It handles **both** the deps (conductor CLI / pandoc / marp) **and** the Conductor server:

```bash
gtm-install
```

`gtm-install` is interactive. For each missing piece it asks before doing anything. For the Conductor server specifically, it offers three choices:

1. **You already have a server** — provide the URL (e.g. `http://localhost:8080/api`, or your Orkes Cloud cluster URL).
2. **Start one locally for me** — the script runs `conductor server start`, checks port 8080 first, and falls back to 8081 / 8090 / 9080 / 18080 if 8080 is taken. The OSS jar (~600 MB) downloads once on first run. After boot, the script prints the `export CONDUCTOR_SERVER_URL=...` line for you to add to your shell rc file.
3. **Skip for now** — useful if you only want to install the skill files and configure later.

Re-runnable and idempotent. If you set `CONDUCTOR_SERVER_URL` ahead of time, the prompt is skipped.

For **Orkes Cloud** (authenticated remote servers), set the auth env vars yourself before `gtm-install`:

```bash
export CONDUCTOR_SERVER_URL="https://<your-cluster>.orkesconductor.io/api"
export CONDUCTOR_AUTH_KEY="<your-key-id>"
export CONDUCTOR_AUTH_SECRET="<your-key-secret>"
gtm-install
```

For **OSS Conductor** (local or self-hosted), no auth is needed.

To remove:

```bash
gtm-uninstall                              # remove symlinks from every platform it was installed to
npm uninstall -g @conductor-skills/gtm     # remove the package itself
```

### Manual install (from source)

If you'd rather clone the repo and link it directly (e.g., for development):

```bash
git clone https://github.com/conductoross/awesome-skills.git
cd awesome-skills/gtm-mavericks

# Set Conductor connection
export CONDUCTOR_SERVER_URL="http://localhost:8080/api"

# Bootstrap deps interactively (will prompt for conductor CLI, pandoc, marp)
./scripts/install_check.sh

# Register workflows
./scripts/register_workflows.sh

# Link into Claude Code
ln -s "$(pwd)" ~/.claude/skills/gtm-mavericks
```

`install_check.sh` flags:
- (default) interactive — prompt before each install
- `--non-interactive` — check only, never install
- `--auto-install` — install everything possible without prompting

### Verify Claude Code can see it

Open Claude Code in any project. In a new conversation, type:

```
/skills
```

You should see `gtm-mavericks` in the list. If not, restart Claude Code or check the install path.

---

## Test it out locally

### Quick smoke test (no real workflow)

Verify the skill loads and answers correctly:

```
User: list the marketing personas in gtm-mavericks
```

Claude should respond with the six personas (Draper, Jobs, Ogilvy, Clow, Halbert, Dunford) and their `panel_role` from the persona files.

### Full run — Mode A (new product)

Start a fresh Claude Code session. Try a prompt like:

```
let's run a gtm for a new product. I want to build a Notion-for-podcasters — a writing
app where the editor outputs both a script and a synced shownotes doc. No traction yet,
no customers, no website. I have a few sketches but nothing formal.
```

Expected behavior:

1. Claude runs the intake wizard conversationally — one question at a time.
2. After intake, it starts the Conductor workflow and tells you it's running discovery.
3. The workflow runs autonomously (~30–60 min). You can ask "where are we?" at any time.
4. At each phase boundary (ICP, positioning, voice pick, final), Claude renders the artifact inline and asks: approve / revise / reject.
5. On completion, deliverables land in `gtm-output/<run-id>/`.

### Inspecting workflow state directly (optional)

If you want to peek under the hood:

```bash
# Find your active run:
cat .gtm/active-run

# Get the workflow ID:
cat .gtm/runs/<run-id>/state.json

# Inspect in Conductor:
conductor workflow get-execution <workflowId> -c
```

The Conductor UI is also useful — typically at the same host as `CONDUCTOR_SERVER_URL` without the `/api` suffix (e.g., `http://localhost:8080`).

### Resuming after walking away

Close Claude Code. Come back hours/days later. Open a new session and say:

```
where are we on the gtm run?
```

The skill reads `.gtm/active-run`, queries Conductor, and gives you a plain-English summary plus any pending gate.

---

## Examples — prompts you can paste

Copy any of these into Claude (or whichever agent you use) to trigger the skill. The skill will run the intake wizard from there, one question at a time.

### 1. New product, no traction yet (Mode A)

> Let's run a gtm for a new product. I'm building **FlightCalm** — an iOS app that uses Apple Watch heart-rate variability to trigger personalized breathing exercises mid-flight for people with flight anxiety. No traction yet. I have 4 interview transcripts in `~/Desktop/flightcalm/interviews/` and a one-pager concept doc.

What happens: intake wizard → Mode A confirmed → discovery (with corpus + web search) → ICP panel → ICP gate → positioning panel → positioning gate → messaging house → asset voice gate → assets → bundle + PDF.

### 2. Repositioning a B2B SaaS that hit a plateau (Mode B)

> We sell **Hublink** — async-first team workspace. $8M ARR, Series B. Win rate dropped 15% YoY against Linear/Notion. Demos land but deals stall. We need to reposition. I'm uploading lost-deal transcripts and current website copy. Run a full repositioning.

What happens: Mode B → discovery focused on current-positioning audit + lost-deal patterns → 6-persona ICP panel that argues over who the *real* buyer is now → positioning panel surfaces "broaden vs narrow the category" forks → messaging house with anti-messaging that names what to stop saying → assets in Dunford's voice (B2B operational default).

### 3. Launch campaign with positioning already set (Mode C)

> Launch campaign for **Earnpay Advance** — instant earned-wage access for hourly workers, just approved in 12 states. Positioning is set: "Cash you've earned, before payday — no fees, no credit check, no debt." Buyers are 22-38 hourly workers earning $15-25/hr at retail/food service. I need messaging house, landing copy, ad copy variants, and a 4-email outbound sequence in Halbert's direct-response voice.

What happens: Mode C → skips ICP/positioning debate → discovery focused on channels + trigger events → messaging house → voice pick (Halbert recommended for direct-response) → 4 assets generated in his voice → bundle + PDF.

### 4. Mid-run check-in

> Where are we on the GTM run?

What happens: the skill reads `.gtm/active-run`, queries Conductor, and translates the workflow state into plain English ("we're 40% through, ~12 min in, the panel is debating positioning; want to see the ICP draft now?").

### 5. Force a specific persona voice on assets

> When you get to the asset voice pick, use Draper — the emotional-truth one. I want headlines, not bullet lists.

What happens: at the voice gate, the skill commits to Draper for `artifact_generation`. Outbound sequences, ad copy, and landing copy all carry his signature moves (the reframe, lead with feeling, no proof points above story).

### 6. Pause a long-running run

> Pause the run. I'll come back to it tomorrow.

What happens: `conductor workflow pause <id>`. Resume with "resume the gtm run" any time.

### 7. Iterate on positioning without re-running everything

> The positioning we just landed is good but I want to test a category-creation play instead. Can we re-run positioning with that frame?

What happens: the skill terminates the current run, kicks off a new one with `positioning_hypothesis` carrying the category-creation framing, and tells you when the new positioning is ready for review.

### 8. Get just the deliverables, no debate

> Give me messaging house + landing copy + 3 ad copy variants for **<product description>**, voice: Dunford. Skip the long synthesis loops.

What happens: Mode C intake with `max_synthesis_iterations: 1`, deliverables narrowed to the 3 requested. Run completes in ~10-15 min instead of 30-60.

---

## What you'll get

When a run completes, you'll find in `gtm-output/<run-id>/`:

- `gtm-full.md` — assembled 3-tier doc: Executive Summary → Part 1 Deliverables → Part 2 Appendix
- `gtm-full.pdf` — rendered by Conductor's `GENERATE_PDF` task (no local pandoc required)
- `bundle.json` — all artifacts as structured JSON for downstream tooling
- `executive_summary.json` — TL;DR, key decisions, 90-day action plan, KPIs, risks as structured JSON
- `gtm-deck.pdf` / `gtm-deck.html` — if Marp is installed and slides were requested

---

## Customization

### Editing personas

All persona definitions are plain markdown in `gtm-mavericks/references/personas/`. Edit them however you want — frontmatter (YAML) + structured body sections. Changes apply to the *next* run, not in-flight ones (personas are sealed into workflow input at start).

### Adding a 7th persona

1. Create `gtm-mavericks/references/personas/<name>.md` following the same schema as `draper.md`.
2. Update `gtm-mavericks/references/workflow-definitions/gtm_mavericks_v1.json` to add the new persona to both `icp_panel` and `positioning_panel` FORK_JOINs.
3. Re-register the workflow: `./gtm-mavericks/scripts/register_workflows.sh`.

### Output templates

All templates are markdown with `{{double-brace}}` placeholders in `gtm-mavericks/references/output-templates/`. Tweak headers, ordering, branding as needed.

---

## Troubleshooting

**`install_check.sh` says `conductor CLI not found`**
Install it: `npm install -g @conductor-oss/conductor-cli`. If you don't have npm, install Node first (`brew install node` on macOS).

**`install_check.sh` says `CONDUCTOR_SERVER_URL not set`**
Export it in your shell: `export CONDUCTOR_SERVER_URL="http://localhost:8080/api"`. Add to `~/.zshrc` to persist.

**`register_workflows.sh` errors with 401**
Your Conductor server requires auth. Set `CONDUCTOR_AUTH_KEY` and `CONDUCTOR_AUTH_SECRET` (Orkes Cloud key/secret pair), or set `CONDUCTOR_PROFILE` to a saved CLI profile.

**Claude Code doesn't see the skill**
- Confirm the path: `ls -la ~/.claude/skills/gtm-mavericks/SKILL.md`
- Restart Claude Code
- Check `/skills` in a Claude Code session

**Workflow registration fails with "task type LLM_TEXT_COMPLETE not supported"**
You're running OSS Conductor without the LLM task plugin. Two options:
- Switch to Orkes Conductor (Cloud or self-hosted), which has built-in LLM tasks
- Replace `LLM_TEXT_COMPLETE` tasks with `SIMPLE` tasks fronted by a custom worker that calls Claude / OpenAI APIs (an upgrade path is noted in the spec under "Open questions for implementation")

**The persona files seem too brief — can I make them longer?**
Yes. The schema is just a guide. Anything you put in `operating_principles`, `evaluation_questions`, `signature_moves`, `anti_patterns`, `voice_samples`, and `panel_contribution` will be ingested verbatim by the workflow.

**PDF output is missing**
Install pandoc (`brew install pandoc`) and a PDF engine (`brew install --cask basictex` for xelatex on macOS, or `pip install weasyprint`). The skill will skip PDF rendering silently if neither is available — you still get full markdown output.

**The workflow completed but Claude isn't surfacing the checkpoint**
Make sure you're in the *same* Claude Code project where you started the run (the `.gtm/active-run` file lives in your CWD). Try: `cat .gtm/active-run` to confirm a run ID exists. If it's missing, run `/gtm list` in Claude Code to find the run and resume. All checkpoints are conversational — the workflow runs end-to-end; Claude surfaces artifacts at phase boundaries and asks for approval.

---

## Project structure

```
gtm-mavericks/                              ← the skill itself
├── README.md                               ← you are here
├── SKILL.md                                ← Claude Code skill definition
├── references/
│   ├── personas/                           ← 6 marketing maverick persona files
│   ├── workflow-definitions/               ← Conductor workflow JSON (ships ready to register)
│   ├── artifact-schemas/                   ← JSON schemas for each artifact type
│   ├── prompt-templates/                   ← LLM prompts for each workflow phase
│   └── output-templates/                   ← markdown templates for rendered deliverables
├── scripts/
│   ├── install_check.sh                    ← dependency check + auto-install
│   ├── register_workflows.sh               ← PUT-array upsert of all 4 workflow defs
│   ├── build_workflow.py                   ← canonical idempotent patcher
│   ├── render_outputs.sh / .py             ← post-run: fetch workflow output, write files
│   ├── render_pdf.sh                       ← optional: re-render markdown with pandoc
│   └── render_slides.sh                    ← optional: marp → slides
└── examples/                               ← 3 reference walkthroughs (mode A/B/C)
```

---

## License

TBD. Add a `LICENSE` file before sharing publicly.
