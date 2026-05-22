# GTM Mavericks — design doc

**Status:** living document. Updated when the workflow, skill, or persona contract changes.
**Audience:** anyone extending the workflow, debugging a stuck run, writing a new persona, or trying to understand *why* a piece is built the way it is.
**Companion docs:** [`SKILL.md`](../../SKILL.md) is the operator's contract. [`README.md`](../../README.md) is the marketing front door. This doc is the engineering reference.

---

## 1. What this is

gtm-mavericks runs a deep go-to-market workflow on behalf of a non-technical operator (PMM, founder, marketing lead). The actual multi-phase research, refinement, and synthesis runs in a [Conductor](https://orkes.io/content/) workflow on a long-running server. The skill is the conversational front door: it collects intake, launches the workflow, translates state into plain English, surfaces artifacts at phase boundaries, and assembles final deliverables.

The differentiator is the **panel of six marketing legends** — Don Draper, Steve Jobs, David Ogilvy, Lee Clow, Gary Halbert, April Dunford — encoded as structured operating systems rather than personas in a costume sense. They argue over ICP and positioning, and disagreements are preserved as **strategic forks** in the output rather than smoothed away.

### 1.1 Design principles

1. **Disagreement > consensus.** Six perspectives that argue produce sharper strategy than one that smooths to averages. The bundle preserves every panel disagreement in Part 2 (the appendix).
2. **Personas as operating systems.** Each persona is a markdown file with structured fields that define the persona contract. The current v1 workflow embeds distilled persona rules directly in task prompts; those prompts should be kept aligned with the markdown contract.
3. **Operator decides.** Strategic forks are preserved as choices, never auto-resolved. The skill never decides for the operator on a real tradeoff.
4. **Audit-friendly.** Every line of the executive summary traces back through a decisions log to a panel critique or a recorded fork.
5. **OSS-portable.** The skill must run end-to-end on Conductor OSS without proprietary plumbing — no external prompt registry, no proprietary search APIs, no commercial-only task types.
6. **Substance over style.** The maverick framing only works because the underlying GTM rigor is real. Theatre is forbidden.

### 1.2 Non-goals

- **Real-time interactive workflow execution.** The workflow runs unattended for 30–60 min; the skill does not coordinate fine-grained streaming between the user and individual LLM calls.
- **Pause-on-gate as the default UX.** All four "gates" are INLINE pass-throughs (see §6.4). The skill can `pause` a run on user request but does not implicitly halt at every phase boundary.
- **Multi-tenant orchestration.** A single Conductor server. No tenant isolation, no quotas.
- **Generating arbitrary asset types.** The workflow ships with four asset types — sales playbook, landing copy, ad copy, outbound sequences. Adding a fifth is a workflow JSON edit, not a runtime feature.

---

## 2. System architecture

```
                   ┌─────────────────────────────────────────────────┐
                   │  User (operator: PMM / founder / marketing lead)│
                   └──────────────────┬──────────────────────────────┘
                                      │ plain English
                                      ▼
                   ┌─────────────────────────────────────────────────┐
                   │  Coding agent (Claude Code / Codex / Gemini / …)│
                   │   ─────  loads SKILL.md  ─────                  │
                   │   • intake wizard                               │
                   │   • status translation                          │
                   │   • opportunistic artifact review               │
                   │   • finalization                                │
                   └──────┬──────────────────────────────┬───────────┘
                          │ conductor CLI               │ Read/Write
                          │ (workflow start, status,    │ (.gtm/, gtm-output/)
                          │  pause, terminate)          │
                          ▼                              ▼
        ┌────────────────────────────────────┐    ┌─────────────────┐
        │  Conductor server (OSS or Orkes)   │    │  Local FS       │
        │  • 4 workflow defs (main + 3 sub)  │    │  • run state    │
        │  • LLM_CHAT_COMPLETE task          │    │  • intake JSON  │
        │  • GENERATE_PDF task               │    │  • bundles      │
        │  • SUB_WORKFLOW, FORK_JOIN, etc.   │    │  • PDFs         │
        └────────────┬───────────────────────┘    └─────────────────┘
                     │ Anthropic API
                     │ (model + web_search tool)
                     ▼
        ┌────────────────────────────────────┐
        │  Anthropic (claude-{haiku|sonnet|  │
        │  opus}-N + web_search server tool) │
        └────────────────────────────────────┘
```

### 2.1 Trust boundaries

- **User ↔ Skill:** plain English. No tool IDs, no JSON, no task references.
- **Skill ↔ Conductor:** the `conductor` CLI is the **only** sanctioned interface. Two bootstrap scripts (`install_check.sh`, `register_workflows.sh`) are the only place a raw HTTP client touches the Conductor API, and only for documented quirks (PUT-array upsert, token minting).
- **Conductor ↔ Anthropic:** via Conductor's native Anthropic provider. The `ANTHROPIC_API_KEY` lives on the Conductor server, not the client. The skill never holds it.
- **No external search keys.** Discovery research uses Anthropic's `web_search` tool, not Brave / Google CSE / etc. There are no legacy `search_provider` / `search_api_key` parameters.

### 2.2 Why Conductor

The workflow needs durable execution: 30–60 min of LLM work with multiple long-running tool calls (web_search can take minutes per call), survives client disconnects, restartable, observable. Doing this in a single Anthropic API call hits context limits and provides no checkpoints; doing it in a Python script loses durability and observability. Conductor gives us:

- Durable task execution (the workflow survives skill restarts).
- Native LLM task type with structured retries and per-task timeouts.
- FORK_JOIN / DO_WHILE / SWITCH primitives for the multi-persona + iteration patterns.
- Native PDF generation (`GENERATE_PDF`) — no local LaTeX or pandoc.
- A REST API + CLI that the skill can drive without bespoke transport code.

OSS Conductor is sufficient. Commercial Orkes adds auth and dashboards but doesn't change the workflow.

---

## 3. Components

### 3.1 The skill (`SKILL.md`)

The skill is markdown with YAML frontmatter, designed to load directly into Claude Code, Codex CLI, Gemini CLI, OpenCode, or any agent that reads agent-skill files. It encodes:

- **Non-negotiable rules** (use the `conductor` CLI, never Docker, never curl the API).
- **Intake wizard** — 7 questions, one at a time, with validation rules.
- **Run lifecycle** — generating run-ids, writing state, launching workflows, supporting concurrent runs.
- **Status translation** — a mapping table from `taskReferenceName` to user-facing phase + approximate progress.
- **Error recovery** — three failure-class tables (intake validation, LLM/provider, infrastructure).
- **Artifact review** — when to surface ICP / positioning / messaging house mid-run vs at completion.
- **Finalization** — running `render_outputs.sh`, opening the PDF, summarizing deliverables.

The skill does **not** decide marketing strategy on its own. It's the conversational front door to the workflow; the workflow does the strategy work.

### 3.2 Workflow definitions

Four Conductor workflow JSONs live in `references/workflow-definitions/`:

| Workflow | Purpose |
|---|---|
| `gtm_mavericks_v1.json` | Main 25-task workflow. Wires intake → mode-routed discovery → ICP panel + synthesis → positioning panel + synthesis → messaging house → asset generation → bundle → executive summary → markdown + PDF render. |
| `discovery_new_product.json` | Sub-workflow for Mode A (launching new). Web-search-driven market discovery, customer signals, category framings. |
| `discovery_reposition.json` | Sub-workflow for Mode B (repositioning). Current-positioning audit, lost-deal patterns, competitive landscape. |
| `discovery_campaign.json` | Sub-workflow for Mode C (campaign). Trigger-event analysis, channel audit, audience receptivity. |

All four register via `PUT /api/metadata/workflow` (PUT-array upsert; see §10.4).

### 3.3 Personas

Six markdown files in `references/personas/`, one per maverick: `draper.md`, `jobs.md`, `ogilvy.md`, `clow.md`, `halbert.md`, `dunford.md`.

Each file has YAML frontmatter (name, era, domain, b2b_fit, b2c_fit, panel_role) and structured sections that define what the workflow prompts should apply:

| Section | Content | How the workflow uses it |
|---|---|---|
| `operating_principles` | The persona's worldview as ~7 numbered claims. | Source material for panel-task prompt rules. |
| `evaluation_questions` | The ~6 questions this persona asks every artifact. | Source material for ICP / positioning critique instructions. |
| `signature_moves` | Reusable techniques (Draper's "it's toasted" reframe, Halbert's offer-first structure). | Source material for asset-generation voice instructions. |
| `anti_patterns` | What this persona *refuses* — corporate jargon for Halbert, feature comparisons for Jobs, etc. | Source material for refusal and anti-messaging rules. |
| `voice_samples` | 2–3 short writing samples in the persona's voice. | Source material for judge and voice-fidelity prompts. |
| `panel_contribution` | One paragraph on what this persona uniquely brings. | Source material for the synthesis prompt's panel-balance context. |

The structured-fields approach is what makes the panel produce distinguishable outputs. If you write "be Draper" in the prompt, you get vague AI-generated copy that resembles every other persona. If you write "apply these concrete evaluation questions and refuse these anti-patterns," you get arguably-Draper. In v1, those rules are embedded in workflow JSON task messages rather than read dynamically from markdown at runtime.

### 3.4 Prompt templates

Per-phase prompts in `references/prompt-templates/`:

| Prompt | Used by |
|---|---|
| `discovery-{new-product,reposition,campaign}.txt` | The single `LLM_CHAT_COMPLETE` task in each discovery sub-workflow. Inlined with `webSearch: true`. |
| `socratic-probe.txt` | The Socratic adversarial probe step inside every synthesis loop (§6.5). |
| `icp-synthesis.txt` | The synthesis prompt for the ICP loop. |
| `positioning-synthesis.txt` | The positioning loop synthesis prompt. |
| `messaging-house.txt` | The messaging house loop synthesis prompt. |
| `asset-generation.txt` | The variant-generation prompt (one call per voice per asset). |
| `asset-judge.txt` | The judge LLM that picks across 3 voice variants per asset. |
| `bundle-artifacts.txt` | (legacy — bundle is now an INLINE graaljs merge; see §6.7) |
| `persona-panel-critique.txt` | (used by panels via `panel_contribution`). |

All prompts are **inlined directly into the workflow JSON** at `inputParameters.messages`. There is no Conductor prompt registry, no `setup_prompts.sh`. This keeps the workflow self-contained and OSS-portable.

---

## 4. Data flow

The shape that flows through the workflow:

```
intake.json
   │
   ▼ normalize_intake (validation + defaults)
   │
   ▼ mode_router (SWITCH on mode)
   │
   ├── discovery_new_product   ──┐
   ├── discovery_reposition    ──┤   each emits {discovery: {...}}
   └── discovery_campaign      ──┘
   │
   ▼ discovery_normalize (INLINE — unifies whichever ran)
   │
   ▼ icp_panel (FORK_JOIN of 6 personas)
   │
   ▼ icp_synthesis_loop (DO_WHILE: draft → Socratic probe → revised draft)
   │
   ▼ icp_synthesis_loop_latest (INLINE salvage)
   │
   ▼ gate_icp_review (INLINE pass-through; skill can pause here)
   │
   ▼ positioning_panel (FORK_JOIN of 6 personas)
   │
   ▼ positioning_synthesis_loop (DO_WHILE same shape)
   │
   ▼ positioning_synthesis_loop_latest (INLINE salvage)
   │
   ▼ gate_positioning_review (INLINE pass-through)
   │
   ▼ messaging_house_loop (DO_WHILE same shape)
   │
   ▼ messaging_house_loop_latest (INLINE salvage)
   │
   ▼ gate_pick_asset_voice (INLINE pass-through; decorative)
   │
   ▼ artifact_generation (FORK_JOIN of 4 assets × 3 voice variants + judge)
   │
   ▼ bundle_artifacts (INLINE graaljs merge — no LLM)
   │
   ▼ executive_summary (LLM_CHAT_COMPLETE — synthesizes bundle into TL;DR)
   │
   ▼ gate_final_review (INLINE pass-through; sees bundle + summary)
   │
   ▼ render_markdown (INLINE — 3-tier markdown doc)
   │
   ▼ sanitize_markdown (INLINE — Unicode → ASCII)
   │
   ▼ generate_pdf (GENERATE_PDF native task)
   │
   ▼ finalize (INLINE)
   │
   ▼ workflow outputs: { final_bundle, executive_summary, markdown, pdf }
```

### 4.1 Intake payload (canonical)

```json
{
  "run_id": "gtm-20260520-153018-a7c",
  "mode": "new_product",
  "product": {
    "name": "FlightCalm",
    "description": "iOS app using Apple Watch HRV to trigger personalized breathing exercises mid-flight for people with flight anxiety."
  },
  "icp_hypothesis": "Frequent business travelers with flight anxiety, mid-30s to mid-50s.",
  "corpus": {
    "urls": ["https://flightcalm.example.com/landing"],
    "files": [".gtm/runs/gtm-20260520-153018-a7c/inputs/interview1.md"]
  },
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-6",
  "max_synthesis_iterations": 3
}
```

### 4.2 Workflow outputs (after `status: COMPLETED`)

| Output | Type | Source task |
|---|---|---|
| `final_bundle` | full JSON bundle | `bundle_artifacts` |
| `executive_summary` | structured exec summary JSON | `executive_summary` |
| `markdown` | sanitized markdown doc | `sanitize_markdown` |
| `pdf` | `{ location: "file://...", sizeBytes: N }` | `generate_pdf` |

The `render_outputs.sh` script fetches these, writes the bundle/summary/md to disk, and copies the PDF from the file:// location to `gtm-output/<run-id>/`.

---

## 5. The intake wizard

The skill walks the user through 7 questions, one at a time. Validation rules are enforced before the workflow is launched so that recoverable mistakes don't cost a 30-minute run.

| # | Question | Validation | Field |
|---|---|---|---|
| 1 | What are we doing? | Must map to `new_product` / `reposition` / `campaign`. | `mode` |
| 2 | Product name + description | `name` ≥1 char; `description` ≥20 chars **and** describes what / who / unfair angle. | `product` |
| 3 | Who's the buyer? | Free-form. Optional. | `icp_hypothesis` |
| 4 | Materials? | Folder path + URLs (max 10). Optional. | `corpus` |
| 5 | Which model? | One of three tiers or a canonical model ID. | `llm_model` |
| 6 | How many refinement passes? | 1–5; default 3. | `max_synthesis_iterations` |
| 7 | Confirm and launch | One-paragraph summary read back to the user. | n/a |

The validation in step 2 deserves its own callout: the 20-char floor catches one-word answers but not vague filler ("yet another AI app for users" is 28 chars and useless). The three-element check (concrete what, who, angle) is enforced by judgment — if the description doesn't have all three, the skill asks one follow-up before launching. This prevents the workflow's most common failure mode: synthesis tasks hallucinating a product from missing context.

---

## 6. Workflow internals

### 6.1 Mode routing

```
normalize_intake (INLINE)
       │
       ▼
mode_router (SWITCH)
       ├── "new_product"  → discovery_new_product_ref (SUB_WORKFLOW)
       ├── "reposition"   → discovery_reposition_ref  (SUB_WORKFLOW)
       └── "campaign"     → discovery_campaign_ref    (SUB_WORKFLOW)
       │
       ▼
discovery_normalize (INLINE)
       │
       ▼ exposes `discovery_normalize.output.result.discovery` for ALL downstream tasks
```

`mode_router` has no `defaultCase` — if `mode` isn't one of the three valid values, the workflow fails at this step. `normalize_intake` validates `mode` against the three-value whitelist and terminates with `invalid_mode: ...` before `mode_router` ever runs, so the SWITCH never sees an invalid value in practice.

The `discovery_normalize` INLINE task is the canonical handle for downstream tasks. It checks `${discovery_reposition_ref.output.discovery}`, `${discovery_new_product_ref.output.discovery}`, `${discovery_campaign_ref.output.discovery}` in turn, returns the first one that's not the literal unresolved-expression string, and exposes it as `{ discovery: <obj> }`. Downstream references all use `${discovery_normalize.output.result.discovery}` — 29 references across the workflow.

### 6.2 Discovery with web search

Each discovery sub-workflow is a small pipeline:

```
build_fetch_tasks (INLINE — parse corpus URLs into HTTP task templates)
       │
       ▼
fetch_corpus_urls (FORK_JOIN_DYNAMIC HTTP — fetch up to 10 URLs, 12KB cap each)
       │
       ▼
fetch_join (JOIN)
       │
       ▼
build_corpus_content (INLINE — concatenate fetched bodies into a single string for the prompt)
       │
       ▼
synthesize_discovery (LLM_CHAT_COMPLETE with webSearch: true)
```

The LLM call sets `webSearch: true` — Anthropic's server-side `web_search` tool. The LLM does multi-turn research itself: searches, opens pages, follows citations, returns customer signals with citable URLs. A real Mode B run burns ~250K prompt tokens on this step alone.

`webSearch: true` replaces the legacy `search_provider` / `search_api_key` plumbing (Brave / Google Custom Search). The current workflow has no external search dependencies — only `ANTHROPIC_API_KEY` is required on the Conductor server. Legacy fields are still accepted in the intake payload for backwards compatibility but are ignored.

### 6.3 Persona panels (FORK_JOIN of 6)

The ICP and positioning panels each run six personas in parallel:

```
icp_panel (FORK_JOIN)
   ├── icp_draper_ref  (LLM_CHAT_COMPLETE)
   ├── icp_jobs_ref    (LLM_CHAT_COMPLETE)
   ├── icp_ogilvy_ref  (LLM_CHAT_COMPLETE)
   ├── icp_clow_ref    (LLM_CHAT_COMPLETE)
   ├── icp_halbert_ref (LLM_CHAT_COMPLETE)
   └── icp_dunford_ref (LLM_CHAT_COMPLETE)
       │
       ▼
icp_join (JOIN)
```

Each branch sees the same inputs (discovery output + intake product + ICP hypothesis) but its prompt embeds only that persona's distilled rules. The branches don't see each other's outputs; the join collects all six.

The branches run in parallel — typical wall-clock is 1–2 minutes for the whole panel regardless of how many personas (limited by the slowest single call).

### 6.4 Gates are pass-throughs, not pauses

The workflow has four tasks named `gate_*`:

| Task | Purpose | Output |
|---|---|---|
| `gate_icp_review` | Mark "ICP is ready for opportunistic review" | `{ decision: 'approve', artifact: <icp> }` |
| `gate_positioning_review` | Mark "positioning is ready" | `{ decision: 'approve', artifact: <positioning> }` |
| `gate_pick_asset_voice` | Mark "messaging house is ready" — decorative | `{ decision: 'approve', asset_voice: 'dunford' }` (asset_voice is unused) |
| `gate_final_review` | Mark "bundle + exec summary are ready" | `{ decision: 'approve' }` |

All four are INLINE graaljs evaluators that emit `decision: 'approve'` immediately and let the workflow continue. They do **not** halt the workflow waiting for human input. This is intentional:

- HUMAN tasks in OSS Conductor were unreliable in our testing (404 from multiple signal endpoints depending on subsystem state). We replaced them with INLINE pass-throughs.
- The skill provides opportunistic review at the conversational level. If the user asks "show me the ICP" mid-run, the skill pulls `icp_synthesis_loop_latest.output.result.artifact` and renders it inline.
- For real halt-on-gate behavior, the operator can `conductor workflow pause <id>` immediately — the next phase boundary won't execute until they resume.

`gate_pick_asset_voice` is the trickiest one. It emits `asset_voice: 'dunford'`, but **no downstream task reads this field**. The `artifact_generation` FORK_JOIN unconditionally runs all three voices in parallel (Dunford, Halbert, Ogilvy) and a judge LLM picks per asset. The gate's `asset_voice` field is a vestige; treat it as decorative.

### 6.5 Synthesis loops (DO_WHILE with Socratic probe)

Each of the three synthesis loops (ICP, positioning, messaging house) has the same shape:

```
<phase>_synthesis_loop (DO_WHILE; loopCondition controls iteration count)
   │   iteration body:
   │   ┌────────────────────────────────────┐
   │   │ <phase>_synthesis_draft            │  LLM_CHAT_COMPLETE
   │   │   inputs: panel outputs, prior     │  emits artifact JSON
   │   │   iteration's draft, prior probes  │
   │   │             │                      │
   │   │             ▼                      │
   │   │ <phase>_socratic_probe             │  LLM_CHAT_COMPLETE
   │   │   inputs: draft                    │  emits {verdict, probes[]}
   │   │             │                      │
   │   │             ▼                      │
   │   │ parse_probe                        │  INLINE — extract verdict
   │   └────────────────────────────────────┘
   │   loopCondition: iteration < 2 || (iteration < max_iter && !satisfied)
```

The loop guarantees ≥2 iterations (minimum useful refinement), caps at `max_synthesis_iterations`, and exits early if the probe returns `verdict: shippable`.

The Socratic probe has **six probe types** designed to push falsification + extension rather than "more detail please":

1. `challenge_assumption` — "you're assuming X; what if X is false?"
2. `missing_concern` — "this ignores Y; what changes when Y is true?"
3. `evidence_falsifier` — "what observation would falsify this claim?"
4. `extension_implication` — "if this is right, then Z must follow; is Z true?"
5. `weakest_point` — "name the single weakest claim and defend it."
6. `internal_consistency` — "claims A and B both appear; reconcile them."

The probe responds with `verdict: shippable | needs_work` and a `probes: [{type, target, reason}]` array. The draft on the next iteration sees the prior probes and is instructed to address each one — without rebutting them as commentary.

**The recurrence rule.** Some probes are unresolvable (e.g., "what's your CAC?" when there's no historical data). To prevent the loop churning indefinitely, the workflow tracks each `(target, type)` tuple across iterations: if the same probe appears unresolved in 3 separate iterations, it's promoted to `documented_gaps` and stops blocking convergence. The loop can then exit even though that specific probe isn't satisfied.

### 6.6 Asset generation — 3 voices in parallel + judge

```
artifact_generation (FORK_JOIN — 4 branches, one per asset)
   ├── asset_sales_playbook_variants (FORK_JOIN of 3 voices)
   │     ├── asset_sales_playbook_dunford  (LLM_CHAT_COMPLETE)
   │     ├── asset_sales_playbook_halbert  (LLM_CHAT_COMPLETE)
   │     └── asset_sales_playbook_ogilvy   (LLM_CHAT_COMPLETE)
   │            │
   │            ▼
   │     asset_sales_playbook_variants_join (JOIN)
   │            │
   │            ▼
   │     asset_sales_playbook_judge (LLM_CHAT_COMPLETE — picks best of 3)
   │
   ├── asset_landing_copy_variants ... + landing_copy_judge
   ├── asset_ad_copy_variants ... + ad_copy_judge
   └── asset_outbound_sequences_variants ... + outbound_sequences_judge
```

Each variant is generated by an LLM call whose prompt embeds the relevant voice rules. The judge sees all three variants and voice guidance for each persona; it picks the strongest and emits the winner's text plus a one-line reason.

The bundle preserves all three variants per asset, not just the judge's pick — operators sometimes want the Halbert version of a Dunford-judged landing page for outbound re-engagement, or want to A/B the picks across voices.

### 6.7 Bundle → executive summary → render → PDF

The tail of the workflow is deterministic JSON shuffling with one LLM call for the executive summary:

```
bundle_artifacts (INLINE graaljs)
   │ deterministic merge: pulls ICP, positioning, messaging house,
   │ asset_*_judge outputs, panel disagreements, decisions log into one bundle JSON.
   │ No LLM, no token limit.
   │
   ▼
executive_summary (LLM_CHAT_COMPLETE)
   │ takes bundle + intake goal; emits structured JSON:
   │ { tldr, goal, key_decisions[], action_plan[], kpis[], gaps_and_risks[] }
   │
   ▼
gate_final_review (INLINE — sees bundle + summary as separate inputs)
   │
   ▼
render_markdown (INLINE graaljs)
   │ accesses bundle fields BY NAME (b.positioning, b.icp_one_pager, ...)
   │ — never iterates, due to the polyglot proxy bug (§10.1)
   │ produces 3-tier markdown:
   │   Tier 1: Executive Summary (from executive_summary)
   │   Tier 2: Part 1 — Deliverables (from bundle)
   │   Tier 3: Part 2 — Appendix (panel disagreements, rejected ICPs, strategic forks)
   │
   ▼
sanitize_markdown (INLINE)
   │ maps Unicode characters to ASCII so GENERATE_PDF doesn't fail:
   │   ✓ → "ok", em-dash → "--", en-dash → "-", smart quotes → straight quotes, etc.
   │ Final guard: any remaining non-ASCII → "?"
   │
   ▼
generate_pdf (GENERATE_PDF native Conductor task)
   │ Helvetica/WinAnsi encoding. Renders sanitized markdown.
   │ Returns { location: "file://...", sizeBytes: N }
   │
   ▼
finalize (INLINE — last task; trivial pass-through for explicit termination)
```

The reason `executive_summary` is its own LLM call rather than being inlined into `bundle_artifacts` is that `bundle_artifacts` is a deterministic JSON merge — fast, no token limit, no provider dependency. The summary step needs an LLM with the full bundle context and shouldn't pollute the deterministic merge logic.

The reason there's **no `enrich_bundle` step** that merges bundle + summary before rendering: an earlier version tried this, but Conductor's graaljs polyglot proxy can't be enumerated or `JSON.stringify`'d, so the merged object always came back empty (see §10.1). The workaround is to pass bundle + summary as separate named inputs to `render_markdown` and have the renderer access fields by direct property name.

---

## 7. Persona-as-operating-system contract

Each persona file is markdown with YAML frontmatter and seven named sections. Treat these files as the source contract for persona behavior. The current v1 workflow does not read them dynamically at runtime; it embeds distilled persona rules in workflow task messages.

```markdown
---
name: April Dunford
era: 2000s-present, B2B positioning consultant
domain: B2B positioning, category design, sales-led GTM
b2b_fit: very high
b2c_fit: medium
panel_role: B2B operational rigor
---

## operating_principles
1. Positioning is the act of setting the context for your product.
2. Position against the *alternative* the buyer is actually considering — including "do nothing".
3. ...

## evaluation_questions
- Who specifically is this for, by role and situation?
- What alternatives are they considering — including the status quo?
- ...

## signature_moves
- The alternatives-first frame.
- The five-component positioning canvas.
- ...

## anti_patterns
- Vague buyer descriptions ("B2B leaders").
- ...

## voice_samples
> "Positioning is the act of deliberately defining where you fit in the world..."

## panel_contribution
Dunford forces the panel through her five-component canvas...
```

**Why YAML frontmatter and named sections instead of a JSON schema?** Personas need to be hand-editable by non-engineers. Frontmatter + markdown headers is the lowest-friction format. The workflow prompt content should be updated from these sections whenever persona behavior changes.

**Why this works.** When you tell an LLM "be Draper" it returns vague AI-generated copy. When you tell an LLM "apply these six specific `evaluation_questions` and refuse any output that violates these eight `anti_patterns`," the output is structurally constrained. The persona becomes a filter, not a costume.

### 7.1 Adding a new persona

1. Drop a file at `references/personas/<name>.md` matching the structure above.
2. Add the persona to both the `icp_panel` and `positioning_panel` FORK_JOIN branches in `references/workflow-definitions/gtm_mavericks_v1.json`. Each branch is an `LLM_CHAT_COMPLETE` task with `inputParameters.messages` that must embed the persona's distilled rules.
3. Optionally add the persona to the asset variants list (`asset_*_<name>` tasks) and the judge prompt's voice list — required if you want their voice considered for asset generation.
4. Re-register the workflow: `./gtm-mavericks/scripts/register_workflows.sh`.

A 7th persona doesn't require a workflow version bump unless you change task structure beyond adding branches.

### 7.2 Editing an existing persona

`signature_moves` and `anti_patterns` are the highest-leverage sections to edit. In v1, changes must be propagated into `gtm_mavericks_v1.json` and workflows must be re-registered before they affect a run.

---

## 8. Concurrency model

Multiple in-flight runs are first-class. The skill supports them by treating `.gtm/runs/<run-id>/` as the durable source of truth and `.gtm/active-run` as a most-recent-pointer convenience.

```
.gtm/
├── active-run           ← single line: most recently started run-id
└── runs/
    ├── gtm-20260520-153018-a7c/
    │   ├── intake.json
    │   ├── state.json   ← { workflowId, runId, productName, mode, llmModel, startedAt, lastSeenStatus, ... }
    │   └── inputs/
    │       └── interview1.md
    └── gtm-20260520-191204-f3d/
        ├── intake.json
        ├── state.json
        └── inputs/
```

When the user issues a run-scoped command:

- If they named a product ("status for FlightCalm"), match case-insensitively against `productName` in each `state.json`.
- Otherwise, default to the run-id in `.gtm/active-run`.
- If multiple runs are live (`lastSeenStatus` in `RUNNING` or `PAUSED`) and the user didn't disambiguate, list them and ask which.

The 3-char suffix in the run-id (`-a7c`) prevents collisions when concurrent runs land in the same second.

The skill never deletes `state.json` or `intake.json`. The user can `rm -rf .gtm/runs/<run-id>/` manually if they want a run forgotten.

---

## 9. Bootstrap and operations

### 9.1 First-time setup

```bash
# 1. Bootstrap deps + Conductor server (interactive)
./gtm-mavericks/scripts/install_check.sh

# 2. Register all 4 workflow defs (idempotent PUT-array upsert)
./gtm-mavericks/scripts/register_workflows.sh
```

`install_check.sh` is interactive by default. It can be run in `--non-interactive` (check only, exit non-zero on missing) or `--auto-install` (install everything without prompting) modes for CI / scripted setups.

What it checks:

| Component | Required? | If missing |
|---|---|---|
| `npm` | yes | Hard-fail with platform-specific install hint. |
| `conductor` CLI | yes | Offer to install via `npm install -g @conductor-oss/conductor-cli`. |
| `CONDUCTOR_SERVER_URL` (reachable) | yes | Offer (a) provide a URL, (b) start a local server, (c) skip. |
| 6 persona files | yes | Hard-fail (part of the skill, not externally installable). |
| 4 workflow JSON files | yes | Hard-fail. |
| `pandoc` | optional | Warn only — PDF is generated server-side; pandoc is only for local re-renders. |
| `marp` CLI | optional | Warn only — slides are a post-run script. |

If `install_check.sh` starts a local server, it does **not** auto-export `CONDUCTOR_SERVER_URL` into the parent shell (that's a fundamental limitation of any subprocess). The script prints an explicit `export CONDUCTOR_SERVER_URL=...` line; the skill verifies the env var is set on its next shell call and asks the user to paste the export if not.

For Orkes Cloud, set `CONDUCTOR_AUTH_KEY` + `CONDUCTOR_AUTH_SECRET` (or `CONDUCTOR_PROFILE=<name>`) and `register_workflows.sh` will mint a token automatically.

### 9.2 Server interactions

The agent talks to the Conductor server **only** through the `conductor` CLI binary. This is the most important architectural rule and is enforced by SKILL.md as a non-negotiable.

**Banned interfaces:**

- Docker / docker-compose / `docker run` — the skill uses `conductor server start` (a Java + JAR command).
- `curl` / `wget` / `httpie` against the Conductor REST API — the skill uses CLI subcommands.
- Any third-party Conductor client library — only the official CLI.

The two bootstrap scripts (`install_check.sh`, `register_workflows.sh`) are the **only sanctioned bypasses**, and only for documented quirks (PUT-array upsert in §10.4, token minting for Orkes).

This rule exists because every alternate path has caused incidents in the past: Docker-installed Conductor diverged from CLI-installed in API behavior; curl-driven workflow starts bypassed the CLI's auth normalization; third-party libraries lagged on schema changes.

### 9.3 Finalization

`./gtm-mavericks/scripts/render_outputs.sh --run-id <run-id>` fetches the workflow execution, writes the bundle JSON / executive summary JSON / markdown / PDF to `gtm-output/<run-id>/`, and that's it. It accepts a `<workflow_id>` positional argument as an alternative to `--run-id`.

The PDF is generated by Conductor's `GENERATE_PDF` task during the run — no local pandoc / xelatex is required. For re-renders with different styling, regenerate from `gtm-full.md` locally via `scripts/render_pdf.sh` (pandoc) or `scripts/render_slides.sh` (marp).

**Why two output directories?** `.gtm/runs/<run-id>/` is internal skill state (intake JSON, run state, corpus inputs). `gtm-output/<run-id>/` is user-facing deliverables. The split lets the user safely `rm -rf gtm-output/` without breaking conversational resume.

---

## 10. Known issues and Conductor-specific gotchas

The current workflow already accounts for these. This section exists so the next operator doesn't repeat the debugging path.

### 10.1 The graaljs polyglot proxy

When an INLINE (graaljs) task receives a dict from another task via `${other.output.result}`, the value comes through as a **Java polyglot proxy**, not a plain JS object. Three things that DON'T work:

| Operation | Behavior on a proxy |
|---|---|
| `for (var k in v)` | Finds zero keys. |
| `Object.keys(v)` | Unreliable across graaljs versions; often returns `[]`. |
| `JSON.stringify(v)` | Returns `"{}"`. |

What DOES work: **direct property access by known name** (`v.foo`, `v["1"]`).

This is why:
- `render_markdown` accesses bundle fields by name (`b.positioning`, `b.icp_one_pager`, etc.) and never iterates.
- `*_loop_latest` salvage receives each iteration's result as a **separate named** `inputParameter` (`iter1_result`, `iter2_result`, ...) instead of trying to iterate the loop output.
- There's no `enrich_bundle` merge step; bundle + summary are passed separately to `render_markdown`.

**Rule for new INLINE tasks:** never iterate a Conductor-proxied input. Always access fields by name, or pass each sub-field as its own `inputParameter`.

### 10.2 PUT-array is the only reliable upsert

`POST /api/metadata/workflow` returns HTTP 500 "already exists" on re-registration, even with `?overwrite=true`, in our OSS Conductor build. The path that always upserts is **`PUT /api/metadata/workflow` with a JSON array body** containing one or more workflow defs.

`register_workflows.sh` uses this pattern. It also streams the JSON via stdin (`--data-binary @-`) rather than `-d "[$(cat ...)]"` — the latter hits `ARG_MAX` on Linux for the ~297KB main workflow file ("Argument list too long").

### 10.3 SUB_WORKFLOW output propagation (resolved)

Historically `${mode_router.output.discovery}` didn't propagate the discovery sub-workflow's output through the SWITCH task. The current workflow resolves this via the `discovery_normalize` INLINE task after the SWITCH. Downstream tasks always use `${discovery_normalize.output.result.discovery}`, never `mode_router.output` or a specific `discovery_*_ref.output` directly.

### 10.4 GENERATE_PDF and Unicode

Conductor's `GENERATE_PDF` task uses Helvetica / WinAnsi encoding and fails on Unicode characters (✓ U+2713, em-dash, en-dash, smart quotes). The `sanitize_markdown` INLINE task maps the common offenders to ASCII before passing to `GENERATE_PDF`, and a final guard strips any remaining non-ASCII to `?`. If you add new content sources, audit them for new Unicode that needs mapping.

### 10.5 DO_WHILE off-by-one

`DO_WHILE` runs the body BEFORE checking `loopCondition`, so `iteration <= max_iter` actually allows `max_iter + 1` iterations. The current `loopCondition`:

```javascript
if ($.iteration <= 2 || ($.iteration < ($.max_iter && parseInt($.max_iter) > 0 ? parseInt($.max_iter) : 3) && $.satisfied !== true)) {
  true;
} else {
  false;
}
```

Guarantees ≥2 iterations, caps at `max_synthesis_iterations`, exits early on `satisfied: true`.

### 10.6 Late-iteration meta-commentary

Late iterations of synthesis loops sometimes produce meta-commentary ("the JSON above is complete...") instead of JSON. Each loop is followed by an INLINE `<loop>_latest` task that walks iteration outputs backwards and returns the first iteration with a parseable schema. Downstream tasks read from `_latest.output.result.artifact`, never from the loop directly.

The explicit `OUTPUT CONTRACT` header added to each synthesis prompt reduced this from a regular occurrence to an edge case, but salvage stays as a safety net.

### 10.7 Anthropic API: temperature + topP conflict

Claude 4.5+ rejects requests that include BOTH `temperature` and `topP`. The workflow sends only `topP: 1.0` and omits `temperature` everywhere.

### 10.8 INLINE task output wrapping

Conductor wraps INLINE task results under `output.result`. When the workflow uses INLINE gates as pass-throughs, downstream refs MUST be `${gate_*.output.result.artifact}` — NOT `${gate_*.output.artifact}`. The current workflow def is correct; do not "simplify" it.

---

## 11. Examples

Three walkthrough docs live in `examples/`:

- [`mode_a_walkthrough.md`](../../examples/mode_a_walkthrough.md) — brand-new B2C consumer product (FlightCalm).
- [`mode_b_walkthrough.md`](../../examples/mode_b_walkthrough.md) — repositioning a B2B SaaS at $8M ARR (Hublink).
- [`mode_c_walkthrough.md`](../../examples/mode_c_walkthrough.md) — launch campaign with positioning already set (Earnpay).

Each walkthrough has:

- Scenario (1 paragraph)
- Intake answers (the 7 wizard questions)
- "What looks right" at each phase (discovery, ICP panel, positioning, messaging house, assets)
- Pass criteria (binary checks)

Use them as smoke-test rubrics when shipping changes. A successful change should produce output that still passes the pass criteria for each mode.

### 11.1 An example strategic fork (excerpt from `evals/bundle/fixtures/example.bundle.json`)

```
Strategic fork: First Purchase Offer — Single Bar vs. Tasting Flight

Option A — $18 single bar with guarantee.
  Tradeoff: slower subscriber acquisition. Most buyers need 2–3 purchases
  before subscribing, extending CAC payback from 1 month to 3–4. Lower AOV
  means more transactions to break even. Guarantee claim rate is real risk
  at industry-typical 15–20%.

Option B — $39 three-bar tasting flight with guarantee.
  Tradeoff: $39 feels steeper to ICPs who "don't want another $18 mistake"
  (now asking for a $39 mistake). Decision paralysis on origin selection.
  Guarantee exposure is 3x.

Recommendation: Option A.
```

This is what the panel produces when Draper, Halbert, and Dunford actually argue: concrete tradeoffs the operator can reason about, not synthesized-to-average mush.

---

## 12. Testing

Three eval tiers, each progressively slower and more expensive but more diagnostic of real quality.

### 12.1 Tier 1 — static (always cheap)

Run before every commit. ~1 sec, $0.

```bash
python3 evals/runner.py --tier static
```

What it checks:
- Personas: all 6 files parse + have all required sections (`operating_principles`, `evaluation_questions`, `signature_moves`, `anti_patterns`, `voice_samples`, `panel_contribution`).
- Workflow JSONs: all 4 files parse + structurally correct (top-level keys, task ref names match expected, no dangling references).
- Prompts: every prompt referenced by the workflow exists in `references/prompt-templates/`.
- Frontmatter: `SKILL.md`'s YAML frontmatter has required fields and is within length limits.

When tier 1 fails: someone renamed a persona, broke the workflow JSON, deleted a prompt template, or dropped a required schema field. Catch these on every save.

### 12.2 Tier 2 — bundle (grade a real run's output)

Run on a captured fixture. ~30 sec + ~$0.10 per bundle for the LLM judge rubrics.

```bash
# With LLM judges (needs ANTHROPIC_API_KEY)
python3 evals/runner.py --tier bundle --bundle /path/to/bundle.json

# Without LLM judges (faster, no API key)
python3 evals/runner.py --tier bundle --bundle /path/to/bundle.json --no-judge
```

What it checks:

| Group | Checks | Deterministic? |
|---|---|---|
| Schema compliance | Each artifact validates against its JSON Schema (`references/artifact-schemas/`). | Yes |
| Structural rules | ICP has all 5 required fields; positioning has ≥1 strategic fork with real tradeoffs; messaging house has ≥3 proof pillars; anti-messaging is non-empty; ... (~14 rules) | Yes |
| LLM-as-judge rubrics | `icp_specificity`, `positioning_differentiation`, `persona_voice`, `anti_messaging` — Claude Sonnet, sampled 3× per rubric | No |

The LLM judge rubrics live in `evals/bundle/rubrics/<name>.md` as prompts. The judge is told "score 1–5 with reasoning" and the runner averages across 3 samples to reduce variance.

When tier 2 fails: regressed quality on an actual run. The deterministic checks bisect cleanly (broken schema, missing field, etc.). The LLM judges are noisier but trend lines over time are diagnostic.

### 12.3 Tier 3 — e2e (full run + grade)

Run on a release. ~30–60 min + ~$5 per run for the actual workflow execution.

```bash
./evals/e2e/run_e2e.sh evals/e2e/scenarios/mode_a_consumer_app.yaml
```

What it does:
1. Launches a real workflow run against the configured Conductor server using the scenario YAML's intake.
2. Polls until the run completes (or times out at ~75 min).
3. Pulls the bundle and runs tier-2 evals against it.
4. Writes a report.

The three included scenarios:

| Scenario | Mode | Use |
|---|---|---|
| `mode_a_consumer_app.yaml` | A (new product) | Brand-new B2C consumer app smoke test |
| `mode_b_b2b_reposition.yaml` | B (reposition) | B2B SaaS repositioning smoke test |
| `mode_c_fintech_campaign.yaml` | C (campaign) | Fintech launch-campaign smoke test |

Scenarios are kept stable so quality regressions show up as score drops over time. Add a new scenario only when the existing three don't exercise a path you need to test.

### 12.4 Capturing bundles for tier-2 fixtures

After a successful workflow run:

```bash
cp /path/to/.gtm/runs/<run-id>/bundle.json \
   evals/bundle/fixtures/<descriptive-name>.bundle.json
```

Naming: `<mode>_<short-product-name>.bundle.json`, e.g., `mode_b_hublink_reposition.bundle.json`.

If a fixture is from a real customer or partner, **do not commit it.** Add to `.gitignore`. Keep one safe example fixture (`example.bundle.json`) in version control.

### 12.5 CI gates

| Tier | Frequency | Gate |
|---|---|---|
| Static | Every push + PR | Must pass to merge. |
| Bundle (judges) | Nightly against `example.bundle.json` | Reported, not blocking — judge variance is real. |
| E2E | Release branches | Blocking before release. |

The GitHub Actions workflow is in `.github/workflows/gtm-mavericks-evals.yml`.

---

## 13. Limitations

Explicit list of what the workflow **does not** do, by design or by current implementation. Don't promise users any of these.

### 13.1 By design

- **No in-flight revision.** The workflow does not re-run from a specific phase. If the user wants different positioning, they start a fresh run with refined intake.
- **No user-controllable asset voice.** The 3-voice judge model is intentional. The user cannot specify "use only Halbert" at intake; they can edit the workflow def's variants list to change which 3 voices run.
- **No per-asset opt-out at intake.** Every run generates all 4 asset types (sales playbook, landing copy, ad copy, outbound sequences). Token cost is paid regardless of what the user planned to use.
- **No gate-pauses.** The workflow does not implicitly pause at any of the 4 gates. Pause-on-gate behavior requires explicit `conductor workflow pause` from the operator.
- **No notification system.** No email, Slack, or webhook on phase completion or run completion. The operator returns to the agent and asks "where are we" or "is it done."
- **Single Anthropic provider.** OpenAI / Google / local models are not supported. Adding a new provider requires changes to every `LLM_CHAT_COMPLETE` task in the workflow (provider, model, request shape) plus the `web_search` equivalent for discovery.

### 13.2 By current implementation

- **No mid-run revision channel.** Even if the operator pauses, modifies an artifact externally, and resumes, the workflow does not pick up the modification — it continues with whatever was in the upstream task's output.
- **The 12KB-per-URL corpus cap** is a hard limit on user-supplied URL content. Long landing pages get truncated. Workaround: convert the long page to a markdown file in `inputs/` (file inputs aren't capped).
- **The 10-URL corpus cap.** More than 10 URLs and the discovery sub-workflow ignores the overflow. Workaround: pre-curate to the 10 most-representative URLs.
- **`GENERATE_PDF` is Helvetica-only.** Custom fonts / styling require post-run pandoc re-render via `scripts/render_pdf.sh`.
- **No Windows file path support in `render_outputs.sh`.** It opens with `open` (macOS) or `xdg-open` (Linux). On Windows the skill is expected to fall back to printing the path.
- **PDF location is on the Conductor server's filesystem.** Local skill needs filesystem access to that path. For remote Orkes Conductor (where the PDF is on a server you don't have FS access to), `render_outputs.sh` prints the remote URL instead of copying.
- **Persona library is fixed at 6.** Adding a 7th persona requires editing the workflow JSON (FORK_JOIN branches) and re-registering, not a runtime field.
- **The asset variants list is hardcoded to {dunford, halbert, ogilvy}.** Changing it requires a workflow JSON edit. There's no "voice library" abstraction.

### 13.3 Edge cases the skill handles

- Concurrent runs: yes (§8).
- Vague product descriptions: caught by intake validation (20-char floor + three-element check).
- Invalid mode: caught by `normalize_intake` before `mode_router`.
- Stale `--version N` registration: skill auto-retries register-then-start.
- Local server URL not exported into the agent's shell: skill verifies `CONDUCTOR_SERVER_URL` after `install_check.sh` and prompts the user to re-export.
- LLM provider 401 / rate-limit / overload: error-recovery section in SKILL.md routes to `conductor workflow retry` or asks for `ANTHROPIC_API_KEY` verification.

---

## 14. Extension points

### 14.1 Add a new asset type (e.g., "press release")

1. In `gtm_mavericks_v1.json`, add a 5th branch to `artifact_generation` matching the existing 4-asset pattern: `asset_press_release_variants` (FORK_JOIN of 3 voices) + `asset_press_release_variants_join` (JOIN) + `asset_press_release_judge` (LLM_CHAT_COMPLETE).
2. Add a generation prompt for the new asset in `references/prompt-templates/asset-generation.txt` (or a new file referenced from the workflow).
3. Wire the judge output into `bundle_artifacts.expression` so the bundle includes the new asset.
4. Update `render_markdown.expression` to render the new asset in Part 1 of the markdown doc.
5. Add an output template in `references/output-templates/press-release.md.tmpl`.
6. Re-register: `./gtm-mavericks/scripts/register_workflows.sh`.

### 14.2 Change the variant voices (e.g., {dunford, halbert, draper})

1. Edit the 3 variant tasks per asset in `artifact_generation` to use the new voice names (`asset_*_dunford` → keep, `asset_*_ogilvy` → rename to `asset_*_draper`).
2. Update each variant's `inputParameters.messages` system prompt to load Draper's `signature_moves` / `anti_patterns` instead of Ogilvy's.
3. Update the per-asset judge prompt to reference `draper` in its voice list and load Draper's `voice_samples`.
4. Re-register.

### 14.3 Add a new probe type to the Socratic probe

1. Edit `references/prompt-templates/socratic-probe.txt`. Add the new probe type to the enumerated list and give it 2–3 example questions.
2. Update the recurrence rule logic in the parse_probe INLINE task if the new type has different "unresolvable" semantics.

### 14.4 Swap the LLM provider

This is a bigger change. Audit:
- Every `LLM_CHAT_COMPLETE` task — `llmProvider` field + `model` field + request shape (different providers reject different parameter combinations).
- The discovery sub-workflows — they use `webSearch: true` which is Anthropic-specific. Equivalents on other providers (OpenAI tool use, Google grounding) have different shapes.
- The Conductor provider config — `ANTHROPIC_API_KEY` env var has provider-specific siblings.

There is no abstraction layer; the workflow assumes Anthropic. A provider swap is a fork, not a config flag.

---

## 15. Decision log

Major design decisions, the alternative considered, and why we picked the current shape. Useful when revisiting any of these.

| Decision | Alternative considered | Reason |
|---|---|---|
| Conductor workflow over single Python script | Single Anthropic API call orchestrating tool use | Durability (survives client restarts), built-in retries, parallel FORK_JOIN, native PDF task, observable state. |
| `LLM_CHAT_COMPLETE` + `webSearch: true` for discovery | External search API (Brave / Google CSE) | One-step LLM-native research, citable URLs, no extra API key. Reduces moving parts. |
| Inlined task-message prompts | Conductor prompt registry | OSS-portable (no registry config), self-contained workflow JSON. Trade-off: re-register on prompt change. |
| Personas as markdown + structured sections | JSON schema with strict typing | Hand-editable by non-engineers. Markdown is the universal format. |
| Six personas | Three or four | Each persona brings a non-overlapping evaluation question set. Below 6 we lose B2B/B2C balance; above 6 the panel cost balloons without proportional quality gain. |
| `INLINE` gates instead of `HUMAN` tasks | HUMAN tasks with skill signaling | OSS Conductor HUMAN-task signaling is unreliable (404s on multiple signal endpoints). INLINE gates + opportunistic skill review work today. |
| 3-voice judge instead of user-pick voice | User picks voice at messaging-house gate | Removes a UX step; judge produces better per-asset matches than a single committed voice for all 4 assets. |
| Socratic probe with 6 types | Generic "critique" prompt | Generic critics ask for "more detail"; the typed probe pushes falsification and extension, which is what produces strategic forks. |
| Recurrence rule (3 strikes → documented_gaps) | Unbounded iteration until satisfied | Some probes are unresolvable; without the rule, loops churn indefinitely on questions the operator can't answer. |
| Latest-iteration salvage | Use the final iteration's output | Late iterations sometimes produce meta-commentary instead of JSON; salvage walks back to the first parseable iteration. |
| In-Conductor PDF (`GENERATE_PDF`) | Local pandoc / xelatex render | Removes a local toolchain dependency; the PDF is part of the workflow output, not a post-step. |
| `bundle_artifacts` deterministic INLINE | LLM call that produces the bundle JSON | Deterministic, fast (<1 sec), no token limit. The synthesis happens upstream; the bundle is just a merge. |
| `executive_summary` as its own LLM call | Inline summary into `bundle_artifacts` | The summary needs LLM reasoning over the full bundle; mixing it into the deterministic merge would re-introduce an LLM dependency in the critical merge path. |
| Two output directories (`.gtm/` and `gtm-output/`) | Single `gtm-output/` with sub-directories | `.gtm/` is durable skill state (resume across sessions); `gtm-output/` is user-facing deliverables. Separation lets the user `rm -rf gtm-output/` safely. |
| Skill ↔ Conductor over CLI only (no curl, no Docker) | Direct REST API calls | Past incidents from divergent paths. CLI is the only sanctioned interface; bootstrap scripts are the only HTTP exceptions. |

---

## 16. Future work

Known gaps and ideas. None are committed; this is the parking lot.

- **Honor `deliverables` at intake.** Currently a no-op (every run generates all 4 assets). Wrapping each branch of `artifact_generation` in a SWITCH that no-ops if the asset isn't requested would save tokens for users who only want 2 of 4 assets.
- **In-flight artifact revision.** A real "revise" path would require a HUMAN task or a new INLINE task that takes a revision instruction and re-runs the downstream synthesis loop with that instruction injected.
- **Slack/email notification on phase completion.** Currently the `notifications` intake field is unused. Adding a `NOTIFY` task at each gate (or a sidecar polling worker) would let the operator walk away and get pinged.
- **Multi-provider support.** A provider-abstracting LLM task type would let users run on OpenAI / Google. Today it's an Anthropic-only fork.
- **Custom voice library.** Today the variants list is hardcoded in the workflow JSON. A "voice library version" intake field (currently a no-op) could select between different 3-voice combinations defined in a registry file.
- **Better corpus handling.** The 10-URL / 12KB caps are crude. Smart summarization of long URLs (sub-LLM call to compress to 12KB before discovery) would let users feed in longer materials.
- **Mid-run cost estimate.** The skill could compute a rough cost estimate from current token usage and project to completion at the configured model tier.
- **Persona library version field made real.** Today `persona_library_version` is unused. Implementing this would let multiple persona libraries coexist (`v1: 6-maverick classic`, `v2: ABM-focused panel`, etc.).
- **Streaming status updates.** Today status is poll-driven. A WebSocket / SSE channel from Conductor would let the skill push updates instead of polling.

---

## 17. References

- [`SKILL.md`](../../SKILL.md) — operator's contract.
- [`README.md`](../../README.md) — marketing front door.
- [`evals/README.md`](../../evals/README.md) — eval suite details.
- [`references/personas/`](../../references/personas/) — six persona files.
- [`references/workflow-definitions/`](../../references/workflow-definitions/) — workflow JSONs.
- [`references/prompt-templates/`](../../references/prompt-templates/) — inlined prompts.
- [`references/artifact-schemas/`](../../references/artifact-schemas/) — JSON Schema for each artifact.
- [`references/output-templates/`](../../references/output-templates/) — Mustache markdown templates.
- [`references/platform-tools.md`](../../references/platform-tools.md) — tool-name mapping for non-Claude agents.
- [`examples/`](../../examples/) — Mode A / B / C walkthroughs.

**External:**
- Conductor OSS docs — https://orkes.io/content/
- Anthropic web_search tool — provider-side, no client config beyond `webSearch: true`.
- April Dunford, *Obviously Awesome* — the positioning canvas the workflow uses for the synthesis step.
