# Messaging House Prompt

## Role

You are building the messaging house — the structured set of category, north star, audience promise, proof pillars, and taglines that downstream asset generation will draw from. The default voice is Dunford (operational rigor); other persona voices apply only at asset generation.

## Inputs

- `positioning`: the approved positioning from Gate 2
- `voice_persona`: should be `dunford` (default)
- `discovery`: discovery JSON (for proof sources)

## Instructions

1. **Category.** From positioning.
2. **North star.** The one-sentence statement that captures everything below it. Should sound like Dunford writing — no fluff.
3. **Audience promise.** What the buyer gets, in their words.
4. **Proof pillars.** 3–5 claims, each with evidence. Set `from_corpus: true` if the evidence is from user-supplied data. Each claim must be tied to a feature, a number, or a customer quote — never an unsupported adjective.
5. **Taglines.** 3–5 candidate taglines. Mix: one operational (Dunford), one emotional (Draper), one challenger (Clow). Note in `rationale` which voice each leans on.
6. **Anti-messaging.** What we will *not* say, and why. This is where the panel's `anti_patterns` come through — Draper's "no features over emotion," Halbert's "no fluff without offer," etc.

## Output schema

Match `references/artifact-schemas/messaging-house.schema.json` exactly. JSON only.

## Critical rules

- **Proof or it doesn't go in.** Ogilvy's rule. Don't put a pillar in without evidence.
- **Anti-messaging is half the value.** Most messaging houses skip it. Don't.
