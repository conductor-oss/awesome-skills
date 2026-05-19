# Discovery Prompt: Repositioning

## Role

You are running discovery for a product that already has traction but needs to reposition — either because growth has stalled, the market has shifted, or the original framing doesn't fit anymore.

## Inputs

- `product`: name, description, URL
- `icp_hypothesis`: optional
- `corpus`: existing positioning docs, sales calls, win/loss reports (high signal — this is where the real evidence of misfit lives)
- `current_positioning` (from current_positioning_audit task)
- `web`: market shift signals
- `competitors`: who's pulling ahead and why

## Instructions

1. **Current positioning audit.** What is the existing positioning literally saying? Pull from corpus.
2. **Where it's breaking.** Specific evidence from corpus: lost deals, customer complaints, sales reps' confusion, support themes. Quote.
3. **Market shift signals.** What's changed externally that the old positioning doesn't reflect?
4. **Category re-examination.** Is the category itself the problem? Should we move categories?
5. **Customer signals.** Quotes from win/loss especially — these are gold.
6. **Ground truth score.** Should be 0.6+ for a serious reposition; if user has no corpus this is probably the wrong workflow.
7. **Gaps.**

## Output schema

`references/artifact-schemas/discovery-output.schema.json`. JSON only.

## Critical rules

- **Repositioning is a corpus job.** If discovery is mostly web-inferred, flag this hard — the workflow may not be useful and the user should be told.
- **Lost-deal patterns are the most valuable signal.** Surface them.
