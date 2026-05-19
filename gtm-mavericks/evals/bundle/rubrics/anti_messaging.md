# Rubric: Anti-Messaging Quality

## Why this matters

A messaging house without anti-messaging is half-built. Anti-messaging is what makes positioning operational — it tells the team what to *stop* saying. Most messaging houses skip it; ours must not.

## Inputs you'll see

- `messaging_house.anti_messaging` (array of strings)
- `messaging_house.category`, `north_star`, `audience_promise`, `proof_pillars`, `taglines` (for context — anti-messaging should oppose specific things, so it helps to see what we ARE saying)

## Criteria

Grade on a 1-5 scale:

- **5 — Exceptional.** Each anti-messaging entry names a specific phrase, pattern, or claim to *stop* using, with a reason. Where possible, quotes verbatim copy that's being deprecated. Calls out the category-default messaging the brand refuses to fall back to.
- **4 — Good.** Specific patterns named, reasons clear. Maybe one entry is generic.
- **3 — Acceptable.** Identifies a few real don'ts but more abstract than concrete ("don't talk about features" rather than "don't open with 'unlock the power of...'").
- **2 — Weak.** Generic anti-messaging that could apply to any product ("don't be boring", "avoid jargon").
- **1 — Failed.** Empty array, single platitude, or contradicts the messaging house above.

## Pass condition

Score ≥ 3.5 across samples.

## Strong examples

- "Never say 'platform' — every category competitor says it. Replace with the specific job we do (e.g. 'compliance attestation engine')."
- "Don't lead with 'AI-powered.' Our differentiation is human-curated; AI-leading copy actively misrepresents what we sell."
- "Stop using 'the only X you'll ever need' — the deck we audited used this phrase 4 times and the data shows it cost us deals."

## Weak examples

- "Don't be boring"
- "Avoid jargon"
- "Be more direct"

## Auto-deduct triggers

- Entries shorter than 8 words → -1 (probably platitude)
- "Avoid" / "Don't be" without a positive replacement → -1 (advice without alternative)
- Entries that just negate the messaging house ("don't say what's in our pillars") → -2 (tautological)
