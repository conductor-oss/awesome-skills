# Discovery Prompt: Campaign

## Role

Positioning is already set. You are running discovery for a *campaign* — focused on channels, audience trigger events, and the moment of decision.

## Inputs

- `product`: name, description, URL
- `icp_hypothesis`: should be present (positioning is set)
- `corpus`: existing positioning, audience research
- `channels` (from channel_audit task)
- `triggers` (from trigger_event_research task)

## Instructions

1. **Confirm the audience.** Brief — positioning already implies this.
2. **Channel audit.** Where does this audience actually live? Rank channels by likely fit. Cite signal (LinkedIn job posts, Reddit communities, G2 categories, etc.).
3. **Trigger events.** What life or business moments make this audience *ready to buy*? Be specific (e.g., "after they fail an audit," "after a churn spike," "when they hire their first VP of X").
4. **Moment-of-decision.** When the audience is most likely to act — and what they're searching for at that moment.
5. **Existing audience touch points.** Communities, podcasts, newsletters, events.
6. **Ground truth score.**

## Output schema

`references/artifact-schemas/discovery-output.schema.json` (re-use; the `competitors` field becomes "channel-adjacent products" for campaign mode). JSON only.

## Critical rules

- **Channel without trigger event is noise.** Don't list channels without explaining why this audience is *receptive* there.
- **Specificity in triggers.** "After a churn spike" beats "when they have retention problems."
