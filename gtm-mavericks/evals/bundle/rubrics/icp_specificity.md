# Rubric: ICP Specificity

## Why this matters

A good ICP is specific enough that a sales rep could write a cold-email subject line for it without making anything up. A bad ICP ("B2B leaders", "growth-focused teams") is the failure mode this rubric is designed to detect.

## Inputs you'll see

- `icp_one_pager.primary_icp.demographic`
- `icp_one_pager.primary_icp.psychographic`
- `icp_one_pager.primary_icp.trigger_event`
- `icp_one_pager.primary_icp.current_alternative`
- `icp_one_pager.primary_icp.pain_in_their_words`

## Criteria

Grade on a 1-5 scale where:

- **5 — Exceptional.** Demographic includes role + company stage/size + situational filter. Trigger is a specific moment in time (e.g., "after closing Series B," "after a churn spike"). Pain_in_their_words sounds like a real human (informal, specific) — not consultant-speak. Current_alternative names a specific tool or "do nothing" with a reason.
- **4 — Good.** Most fields are specific. Maybe one is slightly vague.
- **3 — Acceptable.** Specific in places, generic in others. A sales rep could mostly work with this but would need to add detail.
- **2 — Vague.** Multiple fields use category-speak ("growth teams", "modern companies"). Pain reads like marketing copy.
- **1 — Useless.** ICP could describe anyone. Pain is platitudes. Trigger is "they realize they have a problem."

## Pass condition

Score ≥ 3.5 across samples.

## Examples

### Strong (would score 5)

> demographic: "VP of Engineering at Series B SaaS companies with 50–150 engineers, who took the role within the last 6 months and inherited a deploy process that takes >2 hours"
> trigger_event: "their first incident retrospective where the root cause is 'deploy was rolled back at 2am'"
> pain_in_their_words: "I'm the new VP and I'm spending half my one-on-ones on infra complaints, but my CEO is asking when we'll ship the AI feature"

### Weak (would score 2)

> demographic: "B2B SaaS leaders focused on growth"
> trigger_event: "they realize their current solution isn't working"
> pain_in_their_words: "we need a better way to scale our team"

### Failing (would score 1)

> demographic: "Forward-thinking companies that value innovation"
> pain_in_their_words: "We need to leverage AI to drive transformation"
