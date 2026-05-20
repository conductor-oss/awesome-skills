# Mode C Walkthrough: Launch campaign with positioning already set

## Scenario

A fintech company has just gotten regulatory approval for a new product. Positioning is set and approved by the exec team. They need launch assets for the next 60 days.

User has: approved positioning doc, ICP brief, brand guidelines.

## Intake

1. *What are we doing?* → C (campaign)
2. *Product?* → "Earnpay Advance — instant earned-wage access for hourly workers, just approved in 12 states."
3. *Buyer?* → ICP brief uploaded.
4. *Materials?* → `./inputs/positioning-approved.md`, `./inputs/icp-brief.md`, `./inputs/brand-guide.pdf`
5. *Model?* → Fast (claude-haiku-4-5-20251001) is fine for campaign work where positioning is already locked.
6. *Refinement passes?* → 2 (Campaign Mode benefits less from deep loops since positioning is given.)

## What "looks right"

### Discovery
- No ICP/positioning debate — workflow skips straight to channel audit.
- Channel audit ranks: TikTok, Instagram, employer benefit channels, gig-worker subreddits — with rationale per channel.
- Trigger events: "missed bill," "unexpected expense," "between paychecks" — concrete moments.

### Messaging house
- Built quickly off the existing positioning. Dunford's operational chassis tends to dominate the synthesis.
- Anti-messaging: should call out anything in brand guide that won't work for the trigger-event audience.

### Assets
- Every asset is generated in three voices in parallel — Dunford, Halbert, Ogilvy — and a judge picks the strongest per asset. For direct-response trigger-event campaigns like Earnpay, Halbert will typically win the consumer landing and ad copy (urgency + offer); Dunford typically wins employer-side outbound (ROI, operational fit).
- Ad copy: 3+ variants per channel with channel-specific tone.
- Outbound sequence (if employer-side): operational, ROI-focused.
- Landing copy: split-friendly — multiple hero variants for A/B.
- All non-winning voice variants stay in `bundle.json` for comparison; pull the Dunford landing variant if you want to A/B against Halbert's pick.

## Pass criteria

- Channel recommendations cite *why* the audience is receptive there.
- Trigger events are specific enough to write subject lines for.
- Asset voice is distinguishable from prior mode runs.
