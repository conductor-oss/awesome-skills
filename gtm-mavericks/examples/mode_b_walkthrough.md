# Mode B Walkthrough: Repositioning a B2B SaaS product

## Scenario

A Series B B2B SaaS company sells "team collaboration software." Growth has plateaued at $8M ARR. Sales reps say the demo lands but deals stall. Win-rates dropped 15% YoY against Linear/Notion. Founder wants to reposition.

User has: 8 lost-deal call transcripts, current website copy, last quarter's sales rep feedback survey, competitor positioning docs.

## Intake

1. *What are we doing?* → B (repositioning)
2. *Product?* → "Hublink — async-first team workspace. Currently positioned as 'team collaboration software.'"
3. *Buyer?* → "VPs of Engineering at 50–500 person tech companies"
4. *Materials?* → `./inputs/lost-deals/`, `./inputs/website-copy.md`, `./inputs/rep-survey.csv`
5. *Model?* → Balanced (claude-sonnet-4-6). Opus 4.7 would be the natural pick for an $8M ARR Series B repositioning bet but is currently incompatible with the Conductor Anthropic adapter (see SKILL.md gotcha #12) — stick with Sonnet until that's patched.
6. *Refinement passes?* → 4 (one extra over default — lost-deal patterns benefit from deeper Socratic probing).

## What "looks right"

### Discovery
- Current positioning audit pulls literal copy from existing website ("the only collaboration tool you'll ever need" or similar).
- Lost-deal patterns surface as themes ("compared to Linear we look too broad," "Notion ate our content side," etc.).
- Ground truth score: 0.7+ (strong corpus).

### ICP panel
- Dunford and Ogilvy lead — Dunford forces specificity in alternatives ("Linear" not "competitors"), Ogilvy demands proof from lost-deals.
- Draper and Clow push for the underlying *frustration* the buyer carries.

### Positioning
- Expect a fork between *broadening* the category vs. *narrowing* and dominating a niche. Forks with real tradeoffs (growth ceiling vs. CAC efficiency).
- Anti-messaging should specifically call out the "we do everything" positioning that's not working.

### Asset voices
- For B2B SaaS like Hublink, the judge will typically pick Dunford (operational, sales-team-executable) or Ogilvy (proof-led) for the landing and ad copy. Halbert variants stay in the bundle for comparison — sometimes useful for re-engagement outbound to stalled deals.

## Pass criteria

- Repositioning explicitly names what to *stop* saying.
- At least one strategic fork tied directly to lost-deal evidence.
- Messaging house's anti-messaging quotes existing copy verbatim that needs to die.
