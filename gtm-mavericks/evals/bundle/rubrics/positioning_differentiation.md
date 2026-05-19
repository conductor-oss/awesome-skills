# Rubric: Positioning Differentiation

## Why this matters

The whole point of running a persona panel is to surface real strategic disagreement — choices the operator must actually make. If positioning has no forks, or the forks are fake ("more emotional vs more rational"), the panel didn't earn its keep.

This rubric grades whether the strategic_forks reflect real, ship-affecting decisions.

## Inputs you'll see

- `positioning.recommended_positioning` (the for/who/our/is_a/that/unlike statement)
- `positioning.strategic_forks` (array of forks with option_a, option_b, tradeoff, recommendation)
- `positioning.category_design`

## Criteria

Grade on a 1-5 scale where:

- **5 — Exceptional.** ≥2 forks, each describing a *different downstream strategy* (channel mix, audience expansion ceiling, brand voice, GTM motion). Tradeoffs name concrete consequences (CAC, growth ceiling, sales cycle length, who you sell to). The user could plausibly argue both sides.
- **4 — Good.** ≥1 fork with a real tradeoff. Recommendation is honest about its risk.
- **3 — Acceptable.** Forks exist but tradeoffs are framed as preferences rather than consequences.
- **2 — Weak.** Forks read like A/B copy variations rather than strategic choices.
- **1 — Failed.** No forks, OR forks are tautological ("more emotional vs more rational" without consequence).

## Pass condition

Score ≥ 3.5 across samples.

## Anti-patterns (auto-deduct 1 point each)

- Tradeoff that says "more X" without specifying *what changes downstream*.
- Two options that could both be true at the same time (not actually a fork).
- Category in `category_design` is the same as a competitor's category (no design effort).

## Examples

### Strong (would score 5)

> fork_name: "Category-creation vs category-incumbent"
> option_a: "Position in a new category 'Trust-First Craft Chocolate' — frees us from Dandelion/Marou comparison, requires us to do education marketing, caps near-term TAM"
> option_b: "Position as 'best in craft chocolate subscriptions' — leverages existing demand signal but constrains messaging to incumbent frame, narrows our share to category economics"
> tradeoff: "Category-creation gives us pricing power and zero-direct-comparison, but content marketing burns 6 months before pipeline; incumbent position closes deals faster but we cap at 20% share of the existing $X market"

### Weak (would score 2)

> option_a: "Lead with emotion"
> option_b: "Lead with proof"
> tradeoff: "A is warmer, B is more credible"
