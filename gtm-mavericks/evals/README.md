# gtm-mavericks evals

Three tiers, each progressively slower and more expensive — but more diagnostic of real quality.

| Tier | What it checks | Cost / time | Needs |
|---|---|---|---|
| **Static** | Skill is well-formed: personas parse, workflow JSON is valid, prompts exist, frontmatter is right | ~1 sec, $0 | Nothing — just the skill directory |
| **Bundle** | A final bundle is good: schemas match, structural rules pass, LLM judges score ICP/positioning/voice rubrics | ~30 sec + ~$0.10 per bundle | A `bundle.json`. `ANTHROPIC_API_KEY` for judge tests (auto-skipped if missing) |
| **E2E** | Full Conductor run on a fixed scenario → tier-2 evals against the output | ~30–60 min + ~$5 per run | Conductor server reachable, scenario YAML, `ANTHROPIC_API_KEY` |

You can run any tier independently. CI typically runs static on every PR, bundle on a captured fixture nightly, and e2e on releases.

## Quick start

```bash
cd evals

# Tier 1 — static (always cheap, run before every commit)
python3 runner.py --tier static

# Tier 2 — bundle (judge a real run's output)
python3 runner.py --tier bundle --bundle /path/to/bundle.json

# Tier 2 without LLM judges (faster, no API key needed)
python3 runner.py --tier bundle --bundle /path/to/bundle.json --no-judge

# Tier 3 — full e2e (one scenario, real Conductor run)
./e2e/run_e2e.sh e2e/scenarios/mode_a_consumer_app.yaml
```

Results land in `results/<timestamp>/` as `report.json` + `report.md`.

## What each tier is good for

**Static** catches the obvious regressions: someone renamed a persona, broke the workflow JSON, deleted a prompt template, dropped a required schema field. Cheap enough to run on every save.

**Bundle** evals are where the real value lives. They take a final `bundle.json` (produced by any completed run) and grade it on:

- **Schema compliance** (deterministic): each artifact validates against its JSON Schema
- **Structural rules** (deterministic): ICP has all 5 required fields; positioning has ≥1 strategic fork with real tradeoffs; messaging house has ≥3 proof pillars; anti-messaging is non-empty
- **LLM-as-judge rubrics** (Claude Sonnet, sampled 3× per rubric):
  - `icp_specificity` — is the ICP specific enough to write a cold email subject line to?
  - `positioning_differentiation` — does positioning surface real tradeoffs, not "more emotional vs more rational"?
  - `persona_voice` — pick a random asset, can the judge identify the committed persona's voice from the voice samples in their persona file?
  - `anti_messaging_quality` — does anti-messaging name specific things to stop saying, with reasons?

Bundle evals are deterministic enough to bisect regressions (e.g., "positioning quality dropped after we changed the synthesis prompt — show me which rubric").

**E2E** is the slow check — a real Conductor run with a fixed scenario, then tier-2 evals on the output. Run before releases. The scenarios are kept stable so quality regressions show up as score drops over time.

## File layout

```
evals/
├── README.md                 ← this file
├── runner.py                 ← entry point; --tier static|bundle|all
├── static/
│   ├── test_personas.py      ← 6 persona files parse + have all schema sections
│   ├── test_workflow_defs.py ← workflow JSONs are valid + structurally correct
│   ├── test_prompts.py       ← every prompt referenced by the workflow exists
│   └── test_frontmatter.py   ← SKILL.md frontmatter is valid
├── bundle/
│   ├── test_schemas.py       ← bundle artifacts validate against JSON Schemas
│   ├── test_structure.py     ← structural rules (forks ≥1, pillars ≥3, etc.)
│   ├── judge.py              ← LLM-as-judge harness; calls Anthropic API
│   ├── rubrics/              ← one .md per rubric (judge reads these)
│   │   ├── icp_specificity.md
│   │   ├── positioning_differentiation.md
│   │   ├── persona_voice.md
│   │   └── anti_messaging.md
│   └── fixtures/
│       └── README.md         ← how to capture and add fixture bundles
├── e2e/
│   ├── run_e2e.sh            ← full-run orchestrator
│   └── scenarios/            ← input fixtures for e2e
│       ├── mode_a_consumer_app.yaml
│       ├── mode_b_b2b_reposition.yaml
│       └── mode_c_fintech_campaign.yaml
└── results/                  ← timestamped run outputs (gitignored)
```

## Adding a new rubric

1. Drop a new `bundle/rubrics/<name>.md` with the rubric body — sections `Criterion`, `Pass condition`, `Examples` (pass / fail).
2. `judge.py` auto-discovers it. No code changes needed.

## Adding a new e2e scenario

1. Drop a YAML at `e2e/scenarios/<name>.yaml` with the intake payload.
2. Run `./e2e/run_e2e.sh e2e/scenarios/<name>.yaml`.

## Pass criteria

The runner exits non-zero if any **static** or **structural** check fails. Judge rubrics produce scores (1-5); a rubric is "passing" if its mean across samples ≥ 3.5. The overall run is "passing" if all static + structural pass AND all rubrics meet threshold.
