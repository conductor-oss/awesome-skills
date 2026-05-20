# Mode A Walkthrough: Brand-new B2C consumer product

This example shows the expected behavior of a Mode A run (launching something new). Use this as a "looks-right" rubric when smoke-testing.

## Scenario

A solo founder is launching a new app that helps anxious frequent flyers manage flight anxiety with biometric-aware in-flight breathing exercises. No traction, no users yet. Founder has: a 1-page concept doc, 4 customer interview transcripts from anxious flyers.

## Intake

1. *What are we doing?* → A (new product)
2. *Product?* → "FlightCalm is an iOS app that uses Apple Watch heart-rate variability to trigger personalized breathing exercises mid-flight for people with flight anxiety."
3. *Buyer?* → "Frequent flyers with flight anxiety, mid-30s to mid-50s, business travelers mostly."
4. *Materials?* → 4 interview transcripts in `./inputs/interviews/`, 1 concept doc.
5. *Model?* → Balanced (claude-sonnet-4-6).
6. *Refinement passes?* → 3 (default).

## What "looks right" at each phase

### Discovery

- Ground truth score: 0.6–0.8 (good corpus from 4 interviews).
- Customer signals: literal quotes from interviews — anxiety triggers, current coping mechanisms ("Xanax," "I just don't fly anymore," etc.).
- Category: should propose multiple framings — "wearable wellness app," "anxiety management tool," "biometric-driven mindfulness." Not just one default.

### ICP panel

- Draper should push for the emotional truth — "the freedom to fly without dread."
- Jobs should push for the experience-first framing — "the breath that replaces the pill."
- Dunford should demand specificity — not "anxious flyers" but "frequent business travelers who have started flying less since 2024."
- Ogilvy should demand corpus quotes for `pain_in_their_words`.
- Halbert should ask about the trigger — "what makes them download the app?"
- Clow should ask if this person *wants* to be the one carrying this app — i.e., is there shame?

### Positioning gate

Expect a clear fork between:
- *Option A: Wellness-first / lifestyle product* (Draper / Clow lead)
- *Option B: Medical-adjacent / clinical-credibility product* (Ogilvy / Dunford lead)

The user should have to actually pick — both have real tradeoffs.

### Assets

Every asset is generated in three voices in parallel — Dunford, Halbert, Ogilvy — and a judge LLM picks the strongest per asset. For B2C consumer wellness like FlightCalm, the judge will typically pick Halbert for the landing page (offer-first: "First flight, free, anxiety-guaranteed or your money back") and Halbert or Ogilvy for outbound (emotional reframe + proof).

The losing variants stay in `bundle.json` for comparison. If the user wants a more lifestyle-led B2C voice (Draper or Clow), that's a workflow-def edit, not an intake field — see the customization section in the main README.

The voices should be *distinguishable* — that's the test. Compare a Dunford landing-page draft against a Halbert one for the same product; if they read the same, something is broken.

## Pass criteria

- ICP is specific enough to write a cold email to.
- Positioning surfaces at least 2 real strategic forks.
- Anti-messaging includes at least 2 things the founder would otherwise have said.
- Assets are distinguishable by voice (if you swap personas and re-run, copy should change meaningfully).
