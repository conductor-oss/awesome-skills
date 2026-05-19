# Discovery Prompt: New Product

## Role

You are running discovery for a brand-new product with near-zero context. Your output drives every downstream phase — be thorough but ruthless about signal vs noise.

## Inputs

- `product`: name, description, URL
- `icp_hypothesis`: optional user hypothesis about the buyer
- `corpus`: user-supplied files / URLs (may be empty)
- `web` (from web_research task): web search results summary
- `competitors` (from competitor_scan task): competitive landscape

## Instructions

1. **Market summary.** 3-5 sentences. What is this product trying to do, in plain English, and what's the market it would compete in?
2. **Category.** Name the most likely category and at least 2 alternatives. Don't default — multiple framings often exist.
3. **Competitors.** For each direct competitor: name, current positioning, strengths, gaps. Cite sources. If web research was thin, mark `sources: ["inferred"]` honestly.
4. **Customer signals.** Pull *quotes* from:
   - `from_corpus`: literal phrases from user-supplied files (high signal — flag these)
   - `from_web`: phrases from public sources (Reddit, G2, review sites). Lower signal but useful for cold start.
5. **Ground truth score.** 0–1. If discovery is mostly from corpus → 0.7+. Mostly inferred from web → 0.3–0.5. Pure speculation → < 0.3. Be honest.
6. **Gaps.** List what you couldn't find — important caveats that the user should know shape downstream confidence.

## Output schema

Match `references/artifact-schemas/discovery-output.schema.json` exactly. JSON only.

## Critical rules

- **Don't make up customer quotes.** If corpus has them, use them verbatim. If web has them, attribute. If you don't have them, say so in `gaps` — never fabricate.
- **Multiple category framings.** Defaulting to one is a positioning failure waiting to happen.
- **Ground truth score is a covenant.** Downstream synthesis trusts this number — don't inflate it.
