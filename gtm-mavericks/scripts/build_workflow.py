"""Canonical idempotent patcher for the GTM Mavericks workflow.

The workflow definition at `references/workflow-definitions/gtm_mavericks_v1.json` is the
source of truth and ships ready to register. This script exists to (a) re-apply all the
known-correct patches on top of an evolving workflow, and (b) document the design
decisions in one place. Run it whenever you've hand-edited the JSON and want to ensure
all the load-bearing details are restored.

What this script enforces:

  1. **Synthesis draft prompts (`*_synthesis_loop_draft`, `messaging_house_loop_draft`)**
     must include the OUTPUT CONTRACT header that forces JSON on every iteration. The
     LLM otherwise lapses into 'Probe N addressed by...' commentary on iteration 2+.

  2. **Salvage tasks (`*_loop_latest`)** must read each iteration's draft.result as a
     SEPARATE named inputParameter (iter1_result, iter2_result, ...). Conductor's
     graaljs polyglot proxy can't be enumerated via `for (var k in v)` or stringified
     via `JSON.stringify(v)`; only direct property access works. Named inputs sidestep
     the proxy entirely.

  3. **No `enrich_bundle` INLINE task.** An earlier attempt to merge bundle+summary
     before render_markdown hit the same polyglot proxy bug. Instead, render_markdown
     takes bundle + summary as separate named inputs and workflow outputs expose
     final_bundle and executive_summary separately.

  4. **render_markdown body** is the 3-tier renderer: Executive Summary -> Part 1
     Deliverables -> Part 2 Appendix.

  5. **Tail order**: bundle_artifacts -> executive_summary (LLM) -> gate_final_review ->
     render_markdown -> sanitize_markdown -> generate_pdf -> finalize.

  6. **Workflow outputs**: final_bundle, executive_summary, markdown, pdf.

  7. **Mode A/C routing.** All three modes are wired:
     - mode_router SWITCH has cases for reposition, new_product, campaign.
     - Each routes to the matching discovery_* sub-workflow (all at v1, all use webSearch).
     - A `discovery_normalize` INLINE task sits immediately after mode_router and picks
       whichever ref has output (`discovery_reposition_ref`, `discovery_new_product_ref`,
       `discovery_campaign_ref`). Downstream tasks reference
       `${discovery_normalize.output.result.discovery}` uniformly.
     - The normalize expression avoids the literal `${` substring (Conductor's template
       engine would try to substitute it); uses `v.charAt(0)==='$' && v.charAt(1)==='{'`
       instead.

  Re-running this script is idempotent.
"""
import json
import pathlib

P_MAIN = pathlib.Path(__file__).resolve().parent.parent / "references" / "workflow-definitions" / "gtm_mavericks_v1.json"

VERSION = 1
DESCRIPTION = (
    "GTM Mavericks v1: all three modes wired (reposition/new_product/campaign) via "
    "discovery_normalize INLINE passthrough. webSearch deep research, Socratic probe, "
    "iteration-aware synthesis prompts, named-input salvage, executive summary LLM, "
    "3-tier PDF (Exec Summary / Part 1 Deliverables / Part 2 Appendix). Prompts are "
    "inlined directly in LLM task messages."
)

# ---------------------------------------------------------------------------
# 1. Synthesis draft prompt OUTPUT CONTRACT (forces JSON on every iteration)
# ---------------------------------------------------------------------------

OLD_SYN_HEADER = """## ITERATION CONTEXT
If prior_probe_questions below is non-empty, this is a REFINEMENT iteration — address every blocker + major issue while preserving what worked.
If prior_probe_questions is null/empty, this is iteration 1 — produce the initial synthesis."""

NEW_SYN_HEADER = """## OUTPUT CONTRACT — READ THIS BEFORE EVERY ITERATION

Your output is ALWAYS a single complete JSON object matching the schema below. NEVER prose, narration, commentary, or 'Probe N addressed by X' text. The consumer reads ONLY your JSON output — there is no chat history, no prior draft, no markdown context. You are authoring the artifact from scratch every time.

- Iteration 1 (prior_probe_questions empty): produce the initial synthesis.
- Iteration 2+ (prior_probe_questions populated): re-emit the COMPLETE synthesis with probe feedback applied as input. Every field repopulated, same schema. Treat each iteration as a fresh authoring task that consumes the probes as input — NOT as a delta, change log, or commentary on what was fixed.
- If the prior iteration was already shippable, REPEAT the prior JSON wholesale with any minor refinements applied. Always emit complete JSON. NEVER emit prose.

Start with { and end with } on every iteration."""

SYNTHESIS_DRAFT_REFS = {
    "icp_synthesis_loop_draft",
    "positioning_synthesis_loop_draft",
    "messaging_house_loop_draft",
}


def patch_synthesis_prompts(tasks):
    count = 0
    for t in tasks:
        if t.get("taskReferenceName") in SYNTHESIS_DRAFT_REFS:
            user_msg = t["inputParameters"]["messages"][1]["message"]
            if OLD_SYN_HEADER in user_msg:
                t["inputParameters"]["messages"][1]["message"] = user_msg.replace(OLD_SYN_HEADER, NEW_SYN_HEADER)
                count += 1
            elif NEW_SYN_HEADER in user_msg:
                count += 1  # already patched
        if t.get("type") == "DO_WHILE":
            count += patch_synthesis_prompts(t.get("loopOver", []))
        if t.get("type") == "FORK_JOIN":
            for fork in t.get("forkTasks", []):
                count += patch_synthesis_prompts(fork)
    return count


# ---------------------------------------------------------------------------
# 2. Salvage tasks: walk iterations via named inputs (sidesteps polyglot proxy)
# ---------------------------------------------------------------------------

SALVAGE_EXPR = r"""
function e() {
  function tryParse(v) {
    if (v == null) return null;
    if (typeof v === 'object') {
      // direct property access works on polyglot proxies even when for-in does not
      var copy = {};
      var keys = ['primary_icp','secondary_icps','rejected_candidates','panel_disagreements',
                  'recommended_positioning','strategic_forks','category_design',
                  'category','north_star','audience_promise','proof_pillars','taglines','anti_messaging'];
      var any = false;
      for (var i = 0; i < keys.length; i++) {
        var val = v[keys[i]];
        if (val !== undefined && val !== null) { copy[keys[i]] = val; any = true; }
      }
      return any ? copy : null;
    }
    if (typeof v !== 'string') return null;
    var i2 = v.indexOf('{'), j = v.lastIndexOf('}');
    if (i2 < 0 || j <= i2) return null;
    try { return JSON.parse(v.substring(i2, j+1)); } catch(err) { return null; }
  }
  var slots = [
    {n: 8, v: $.iter8_result},
    {n: 7, v: $.iter7_result},
    {n: 6, v: $.iter6_result},
    {n: 5, v: $.iter5_result},
    {n: 4, v: $.iter4_result},
    {n: 3, v: $.iter3_result},
    {n: 2, v: $.iter2_result},
    {n: 1, v: $.iter1_result}
  ];
  var triedCount = 0;
  for (var idx = 0; idx < slots.length; idx++) {
    var s = slots[idx];
    if (s.v == null) continue;
    triedCount++;
    var parsed = tryParse(s.v);
    if (parsed) return { artifact: parsed, final_iteration: s.n, iterations_tried: triedCount };
  }
  return { artifact: null, final_iteration: null, iterations_tried: triedCount };
} e();
"""

SALVAGE_SPEC = {
    "icp_synthesis_loop_latest": ("icp_synthesis_loop", "icp_synthesis_loop_draft"),
    "positioning_synthesis_loop_latest": ("positioning_synthesis_loop", "positioning_synthesis_loop_draft"),
    "messaging_house_loop_latest": ("messaging_house_loop", "messaging_house_loop_draft"),
}


def patch_salvage(tasks):
    count = 0
    for t in tasks:
        ref = t.get("taskReferenceName")
        if ref in SALVAGE_SPEC:
            loop_ref, draft_ref = SALVAGE_SPEC[ref]
            new_inputs = {
                "evaluatorType": "graaljs",
                "expression": SALVAGE_EXPR,
            }
            for i in range(1, 9):
                new_inputs[f"iter{i}_result"] = "${" + loop_ref + ".output." + str(i) + "." + draft_ref + ".result}"
            t["inputParameters"] = new_inputs
            count += 1
    return count


# ---------------------------------------------------------------------------
# 3. Tail: bundle -> exec_summary (LLM) -> gate -> render -> sanitize -> pdf
# ---------------------------------------------------------------------------

EXEC_SUMMARY_SYSTEM = "You are a senior GTM strategist writing the executive summary for a product GTM plan. Your audience: an executive sponsor or founder who has 5 minutes to decide what to greenlight. The full strategy detail follows; your summary is the first 2 pages they read. Output strict JSON only. Be specific. No hedging. No 'consider X or Y' -- pick one and say why."

EXEC_SUMMARY_USER = r"""Synthesize the GTM bundle below into an executive summary plus an actionable plan.

## Inputs

Mode: ${workflow.input.mode}
Product: ${workflow.input.product.description}
Original ICP hypothesis: ${workflow.input.icp_hypothesis}

Full strategy bundle (ICP, positioning, messaging house, assets, decisions log, panel disagreements, documented gaps):
${bundle_artifacts.output.result}

## Required output schema

Return ONLY this JSON, no markdown fence, no preamble:

{
  "tldr": "<2-3 sentences: the GTM bet in plain English. Who we go after, what we say to them, what the unfair angle is. Concrete, not abstract.>",
  "goal": "<1-2 sentences restating the goal in product/market terms specific to THIS product>",
  "key_decisions": [
    {
      "decision": "<the call made, imperative voice, e.g., 'Lead with developer-first bottom-up GTM via AgentSpan as the wedge'>",
      "rationale": "<1-2 sentences why -- cite the evidence from the bundle (panel input, customer signal, competitive read)>"
    }
  ],
  "action_plan": [
    {
      "action": "<concrete next move in imperative voice>",
      "owner": "<role: PMM, DevRel, Founder, Eng lead, Sales lead, etc.>",
      "timeline": "<one of: 'Week 1-2', 'Week 3-4', 'Month 2', 'Month 3'>",
      "success_criteria": "<measurable outcome>"
    }
  ],
  "kpis": [
    { "metric": "<the metric>", "target": "<concrete number with timeframe>" }
  ],
  "gaps_and_risks": [
    "<the most material gap or risk -- pulled from documented_gaps in the bundle plus your strategist judgment. State the risk AND what to monitor.>"
  ]
}

## Quality bar
- 3-5 key_decisions. The highest-leverage calls only.
- 6-10 action_plan items, sequenced so early ones unblock later ones.
- 4-6 KPIs. Mix leading and lagging.
- 3-5 gaps_and_risks. Most material first.
- Lead the action_plan with the move that will most determine whether the strategy works in 90 days.
- Be specific to THIS product. Generic GTM advice is a failure.

Start with { and end with }."""

EXEC_SUMMARY_TASK = {
    "name": "executive_summary",
    "taskReferenceName": "executive_summary",
    "type": "LLM_CHAT_COMPLETE",
    "inputParameters": {
        "llmProvider": "${normalize_intake.output.result.llm_provider}",
        "model": "${normalize_intake.output.result.llm_model}",
        "maxTokens": 8000,
        "messages": [
            {"role": "system", "message": EXEC_SUMMARY_SYSTEM},
            {"role": "user", "message": EXEC_SUMMARY_USER},
        ],
    },
}

RENDER_MD_EXPR = r"""
function e() {
  function esc(s) {
    if (s == null) return '--';
    if (typeof s !== 'string') {
      try { return JSON.stringify(s); } catch(err) { return String(s); }
    }
    return s;
  }
  // For polyglot proxies, we access fields by name (not enumerate).
  var b = $.bundle || {};
  var summary = $.summary || null;
  if (summary && typeof summary === 'string') {
    try {
      var si = summary.indexOf('{'), sj = summary.lastIndexOf('}');
      if (si >= 0 && sj > si) summary = JSON.parse(summary.substring(si, sj+1));
      else summary = null;
    } catch(err) { summary = null; }
  }
  var out = [];
  out.push('# GTM Strategy -- ' + esc(b.run_id || 'run'));
  out.push('');
  out.push('**Mode:** ' + esc(b.mode || '--'));
  out.push('**Ground truth score:** ' + (b.ground_truth_score != null ? b.ground_truth_score : '--'));
  out.push('');
  out.push('---');
  out.push('');

  // ===== EXECUTIVE SUMMARY =====
  out.push('# Executive Summary');
  out.push('');
  if (summary) {
    if (summary.tldr) { out.push('## TL;DR'); out.push(''); out.push(esc(summary.tldr)); out.push(''); }
    if (summary.goal) { out.push('## Goal'); out.push(''); out.push(esc(summary.goal)); out.push(''); }
    if (summary.key_decisions) {
      out.push('## Key decisions'); out.push('');
      for (var i = 0; i < 20; i++) {
        var d = summary.key_decisions[i]; if (d == null) break;
        if (typeof d === 'string') out.push('- ' + esc(d));
        else out.push('- **' + esc(d.decision) + '** -- ' + esc(d.rationale));
      }
      out.push('');
    }
    if (summary.action_plan) {
      out.push('## 90-day action plan'); out.push('');
      for (var i = 0; i < 20; i++) {
        var a = summary.action_plan[i]; if (a == null) break;
        if (typeof a === 'string') out.push((i+1) + '. ' + esc(a));
        else {
          var line = (i+1) + '. **' + esc(a.action) + '**';
          if (a.owner) line += ' -- *owner:* ' + esc(a.owner);
          if (a.timeline) line += ' -- *by:* ' + esc(a.timeline);
          out.push(line);
          if (a.success_criteria) out.push('   - *Success:* ' + esc(a.success_criteria));
        }
      }
      out.push('');
    }
    if (summary.kpis) {
      out.push('## KPIs to track'); out.push('');
      for (var i = 0; i < 20; i++) {
        var k = summary.kpis[i]; if (k == null) break;
        if (typeof k === 'string') out.push('- ' + esc(k));
        else out.push('- **' + esc(k.metric) + '** -- target: ' + esc(k.target || '--'));
      }
      out.push('');
    }
    if (summary.gaps_and_risks) {
      out.push('## Known gaps and risks'); out.push('');
      for (var i = 0; i < 20; i++) {
        var g = summary.gaps_and_risks[i]; if (g == null) break;
        out.push('- ' + esc(g));
      }
      out.push('');
    }
  } else {
    out.push('*Executive summary not available for this run.*'); out.push('');
  }
  out.push('---'); out.push('');

  // ===== PART 1 DELIVERABLES =====
  out.push('# Part 1 -- Deliverables');
  out.push(''); out.push('*Operator-ready outputs. These are what to ship.*'); out.push('');

  var pos = b.positioning;
  var rp = pos ? pos.recommended_positioning : null;
  if (rp && rp.for) {
    out.push('## Positioning Statement'); out.push('');
    out.push('> **For** ' + esc(rp.for) + ', **who struggle with** ' + esc(rp.who_struggles_with) + ', **' + esc(rp.our_product) + '** **is a** ' + esc(rp.is_a) + ' **that** ' + esc(rp.that) + ', **unlike** ' + esc(rp.unlike) + '.');
    out.push('');
  }
  var cd = pos ? pos.category_design : null;
  if (cd && cd.category_name) {
    out.push('### Category'); out.push(''); out.push('**' + esc(cd.category_name) + '**'); out.push('');
    if (cd.frame_of_reference) { out.push(esc(cd.frame_of_reference)); out.push(''); }
  }
  var mh = b.messaging_house;
  if (mh && (mh.north_star || mh.audience_promise)) {
    out.push('## Messaging House'); out.push('');
    if (mh.north_star) { out.push('### North star'); out.push(''); out.push('> ' + esc(mh.north_star)); out.push(''); }
    if (mh.audience_promise) { out.push('### Audience promise'); out.push(''); out.push(esc(mh.audience_promise)); out.push(''); }
    if (mh.proof_pillars) {
      out.push('### Proof pillars'); out.push('');
      for (var i = 0; i < 30; i++) {
        var pp = mh.proof_pillars[i]; if (pp == null) break;
        var fc = pp.from_corpus ? ' *(from corpus)*' : '';
        out.push('- **' + esc(pp.claim) + '** -- ' + esc(pp.evidence) + fc);
      }
      out.push('');
    }
    if (mh.taglines) {
      out.push('### Taglines'); out.push('');
      for (var i = 0; i < 30; i++) {
        var tl = mh.taglines[i]; if (tl == null) break;
        if (typeof tl === 'string') out.push('- ' + tl);
        else out.push('- **' + esc(tl.tagline || tl.text || '--') + '** -- *' + esc(tl.rationale || '') + '*');
      }
      out.push('');
    }
    if (mh.anti_messaging) {
      out.push('### What we will NOT say'); out.push('');
      for (var i = 0; i < 30; i++) {
        var a = mh.anti_messaging[i]; if (a == null) break;
        out.push('- ' + esc(a));
      }
      out.push('');
    }
  }
  var icp = b.icp_one_pager;
  if (icp && icp.primary_icp) {
    var p = icp.primary_icp;
    out.push('## Primary ICP'); out.push('');
    out.push('**Who:** ' + esc(p.demographic)); out.push('');
    out.push("**What they're like:** " + esc(p.psychographic)); out.push('');
    out.push('**Trigger:** ' + esc(p.trigger_event)); out.push('');
    out.push('**Current alternative:** ' + esc(p.current_alternative)); out.push('');
    out.push("**In their own words:**"); out.push('');
    out.push('> ' + esc(p.pain_in_their_words)); out.push('');
  }
  var artifacts = b.artifacts;
  if (artifacts) {
    out.push('## Asset Library'); out.push('');
    for (var i = 0; i < 30; i++) {
      var a = artifacts[i]; if (a == null) break;
      if (typeof a === 'string') {
        try { var ai = a.indexOf('{'); var aj = a.lastIndexOf('}'); a = JSON.parse(a.substring(ai, aj+1)); }
        catch(err) { continue; }
      }
      if (!a || typeof a !== 'object') continue;
      var atype = String(a.type || 'asset').replace(/_/g, ' ');
      var title = atype.charAt(0).toUpperCase() + atype.slice(1);
      out.push('### ' + title); out.push('');
      if (a.voice_persona) { out.push('**Voice:** ' + a.voice_persona); out.push(''); }
      var items = a.items;
      if (items) {
        for (var j = 0; j < 30; j++) {
          var item = items[j]; if (item == null) break;
          out.push('#### ' + esc(item.name)); out.push('');
          if (item.subject) { out.push('**' + esc(item.subject) + '**'); out.push(''); }
          out.push(esc(item.body)); out.push('');
          if (item.rationale) { out.push('> *Why this works:* ' + esc(item.rationale)); out.push(''); }
          out.push('---'); out.push('');
        }
      }
    }
  }
  out.push('---'); out.push('');

  // ===== PART 2 APPENDIX =====
  out.push('# Part 2 -- Appendix: How we got here'); out.push('');
  out.push('*The reasoning, alternatives considered, and panel debate that produced the deliverables above. Read for context; not required to ship.*'); out.push('');
  if (icp) {
    var sec = icp.secondary_icps;
    if (sec) {
      out.push('## Secondary ICP candidates'); out.push('');
      for (var i = 0; i < 10; i++) {
        var s = sec[i]; if (s == null) break;
        out.push('### ' + esc(s.label || ('Secondary ' + (i+1)))); out.push('');
        if (s.demographic) out.push('- **Demographic:** ' + esc(s.demographic));
        if (s.psychographic) out.push('- **Psychographic:** ' + esc(s.psychographic));
        if (s.trigger_event) out.push('- **Trigger:** ' + esc(s.trigger_event));
        if (s.current_alternative) out.push('- **Current alt:** ' + esc(s.current_alternative));
        if (s.pain_in_their_words) out.push('- **Pain:** ' + esc(s.pain_in_their_words));
        out.push('');
      }
    }
    var rej = icp.rejected_candidates;
    if (rej) {
      out.push('## ICP candidates rejected'); out.push('');
      for (var i = 0; i < 20; i++) {
        var r = rej[i]; if (r == null) break;
        out.push('- **' + esc(r.icp) + '** -- ' + esc(r.why_not));
      }
      out.push('');
    }
    var pds = icp.panel_disagreements;
    if (pds) {
      out.push('## ICP -- Panel disagreements'); out.push('');
      var personas = ['draper','jobs','ogilvy','clow','halbert','dunford'];
      for (var i = 0; i < 20; i++) {
        var pd = pds[i]; if (pd == null) break;
        out.push('### ' + esc(pd.topic)); out.push('');
        for (var kk = 0; kk < personas.length; kk++) {
          var key = personas[kk] + '_view';
          if (pd[key]) out.push('- **' + personas[kk].charAt(0).toUpperCase() + personas[kk].slice(1) + ':** ' + esc(pd[key]));
        }
        if (pd.synthesis_recommendation) { out.push(''); out.push('**Synthesis call:** ' + esc(pd.synthesis_recommendation)); }
        out.push('');
      }
    }
  }
  if (pos) {
    var forks = pos.strategic_forks;
    if (forks) {
      out.push('## Positioning -- Strategic forks considered'); out.push('');
      for (var i = 0; i < 20; i++) {
        var f = forks[i]; if (f == null) break;
        out.push('### ' + esc(f.fork_name || ('Fork ' + (i+1)))); out.push('');
        if (f.option_a) {
          var rec = (String(f.recommendation || '').toLowerCase() === 'a') ? ' (recommended)' : '';
          out.push('**Option A -- ' + esc(f.option_a.label) + '**' + rec); out.push('');
          out.push(esc(f.option_a.positioning)); out.push('');
          out.push('*Tradeoff:* ' + esc(f.option_a.tradeoff)); out.push('');
        }
        if (f.option_b) {
          var rec = (String(f.recommendation || '').toLowerCase() === 'b') ? ' (recommended)' : '';
          out.push('**Option B -- ' + esc(f.option_b.label) + '**' + rec); out.push('');
          out.push(esc(f.option_b.positioning)); out.push('');
          out.push('*Tradeoff:* ' + esc(f.option_b.tradeoff)); out.push('');
        }
        out.push('---'); out.push('');
      }
    }
  }
  var dl = b.decisions_log;
  if (dl) {
    out.push('## Decisions log'); out.push('');
    for (var i = 0; i < 30; i++) {
      var d = dl[i]; if (d == null) break;
      out.push('- ' + esc(d));
    }
    out.push('');
  }
  return { markdown: out.join('\n') };
} e();
"""

RENDER_MD_TASK = {
    "name": "render_markdown",
    "taskReferenceName": "render_markdown",
    "type": "INLINE",
    "inputParameters": {
        "evaluatorType": "graaljs",
        "expression": RENDER_MD_EXPR,
        "bundle": "${bundle_artifacts.output.result}",
        "summary": "${executive_summary.output.result}",
    },
}

SANITIZE_MD_EXPR = r"""
function e() {
  var md = $.markdown || '';
  var pairs = [
    [/✓/g, '[x]'], [/✗/g, '[ ]'], [/—/g, '--'], [/–/g, '-'], [/…/g, '...'],
    [/“/g, '"'], [/”/g, '"'], [/‘/g, "'"], [/’/g, "'"],
    [/→/g, '->'], [/←/g, '<-'], [/↔/g, '<->'],
    [/ /g, ' '], [/•/g, '*'], [/●/g, '*'], [/⭐/g, '*'],
    [/×/g, 'x'], [/≠/g, '!='], [/≥/g, '>='], [/≤/g, '<='],
  ];
  for (var i = 0; i < pairs.length; i++) md = md.replace(pairs[i][0], pairs[i][1]);
  md = md.replace(/[^\x00-\x7F]/g, '?');
  return { markdown: md };
} e();
"""

SANITIZE_MD_TASK = {
    "name": "sanitize_markdown",
    "taskReferenceName": "sanitize_markdown",
    "type": "INLINE",
    "inputParameters": {
        "evaluatorType": "graaljs",
        "expression": SANITIZE_MD_EXPR,
        "markdown": "${render_markdown.output.result.markdown}",
    },
}

GENERATE_PDF_TASK = {
    "name": "generate_pdf",
    "taskReferenceName": "generate_pdf",
    "type": "GENERATE_PDF",
    "inputParameters": {
        "markdown": "${sanitize_markdown.output.result.markdown}",
        "pageSize": "A4",
        "theme": "default",
        "pdfMetadata": {
            "title": "GTM Strategy -- ${workflow.input.run_id}",
            "author": "GTM Mavericks workflow",
        },
    },
}


def patch_tail(wf):
    """Ensure tail order: bundle_artifacts -> executive_summary -> gate_final_review ->
    render_markdown -> sanitize_markdown -> generate_pdf -> finalize.
    Strip enrich_bundle if present.
    """
    # Strip enrich_bundle and the tail tasks we're about to replace
    STRIP = {"enrich_bundle", "executive_summary", "render_markdown", "sanitize_markdown", "generate_pdf"}
    cleaned = [t for t in wf["tasks"] if t.get("taskReferenceName") not in STRIP]

    # Find insertion points
    new_tasks = []
    inserted_summary = False
    inserted_render = False
    for t in cleaned:
        new_tasks.append(t)
        if t.get("taskReferenceName") == "bundle_artifacts" and not inserted_summary:
            new_tasks.append(EXEC_SUMMARY_TASK)
            inserted_summary = True
        if t.get("taskReferenceName") == "gate_final_review" and not inserted_render:
            new_tasks.extend([RENDER_MD_TASK, SANITIZE_MD_TASK, GENERATE_PDF_TASK])
            inserted_render = True

    if not inserted_summary:
        raise SystemExit("bundle_artifacts task missing -- cannot insert executive_summary")
    if not inserted_render:
        raise SystemExit("gate_final_review task missing -- cannot insert render/pdf tail")

    # gate_final_review pass-through should expose bundle + summary
    for t in new_tasks:
        if t.get("taskReferenceName") == "gate_final_review":
            ip = t.get("inputParameters", {})
            ip["bundle"] = "${bundle_artifacts.output.result}"
            ip["summary"] = "${executive_summary.output.result}"
            ip["expression"] = "function e() { return { decision: 'approve', bundle: $.bundle, summary: $.summary }; } e();"
            ip.pop("artifact", None)

    wf["tasks"] = new_tasks


# ---------------------------------------------------------------------------
# 6. Mode routing: wire all three modes via discovery_normalize
# ---------------------------------------------------------------------------

NORMALIZE_EXPR = r"""
function e() {
  function resolved(v) {
    if (v == null) return false;
    if (typeof v === 'string' && v.charAt(0) === '$' && v.charAt(1) === '{') return false;
    return true;
  }
  var d = $.discovery_reposition;
  if (!resolved(d)) d = $.discovery_new_product;
  if (!resolved(d)) d = $.discovery_campaign;
  return { discovery: resolved(d) ? d : null };
} e();
"""

DISCOVERY_NORMALIZE_TASK = {
    "name": "discovery_normalize",
    "taskReferenceName": "discovery_normalize",
    "type": "INLINE",
    "inputParameters": {
        "evaluatorType": "graaljs",
        "expression": NORMALIZE_EXPR,
        "discovery_reposition":  "${discovery_reposition_ref.output.discovery}",
        "discovery_new_product": "${discovery_new_product_ref.output.discovery}",
        "discovery_campaign":    "${discovery_campaign_ref.output.discovery}",
    },
}

def make_discovery_branch(mode, ref_name):
    return [{
        "name": f"discovery_{mode}",
        "taskReferenceName": ref_name,
        "type": "SUB_WORKFLOW",
        "subWorkflowParam": {"name": f"discovery_{mode}", "version": 8},
        "inputParameters": {
            "product": "${workflow.input.product}",
            "icp_hypothesis": "${workflow.input.icp_hypothesis}",
            "corpus": "${workflow.input.corpus}",
        },
    }]


def patch_mode_routing(wf):
    """Ensure mode_router has all three cases and discovery_normalize follows it."""
    # 1. Wire all three SWITCH branches
    for t in wf["tasks"]:
        if t.get("taskReferenceName") == "mode_router":
            cases = t.setdefault("decisionCases", {})
            if "reposition" not in cases:
                cases["reposition"] = make_discovery_branch("reposition", "discovery_reposition_ref")
            if "new_product" not in cases:
                cases["new_product"] = make_discovery_branch("new_product", "discovery_new_product_ref")
            if "campaign" not in cases:
                cases["campaign"] = make_discovery_branch("campaign", "discovery_campaign_ref")
            break

    # 2. Insert discovery_normalize after mode_router if not already there
    existing_refs = {t.get("taskReferenceName") for t in wf["tasks"]}
    if "discovery_normalize" not in existing_refs:
        new_tasks = []
        for t in wf["tasks"]:
            new_tasks.append(t)
            if t.get("taskReferenceName") == "mode_router":
                new_tasks.append(DISCOVERY_NORMALIZE_TASK)
        wf["tasks"] = new_tasks
    else:
        # Ensure the existing normalize task has the correct (non-self-referencing) inputs
        for t in wf["tasks"]:
            if t.get("taskReferenceName") == "discovery_normalize":
                t["inputParameters"]["discovery_reposition"] = "${discovery_reposition_ref.output.discovery}"
                t["inputParameters"]["discovery_new_product"] = "${discovery_new_product_ref.output.discovery}"
                t["inputParameters"]["discovery_campaign"] = "${discovery_campaign_ref.output.discovery}"
                t["inputParameters"]["expression"] = NORMALIZE_EXPR
                break

    # 3. Replace all old discovery_reposition_ref.output.discovery refs (idempotent)
    OLD = "${discovery_reposition_ref.output.discovery}"
    NEW = "${discovery_normalize.output.result.discovery}"

    def replace_refs(tasks, count=[0]):
        for t in tasks:
            if t.get("taskReferenceName") == "discovery_normalize":
                continue  # never replace inside the normalize task itself
            ip = t.get("inputParameters", {})
            for k in list(ip.keys()):
                v = ip[k]
                if isinstance(v, str) and OLD in v:
                    ip[k] = v.replace(OLD, NEW); count[0] += 1
            for m in ip.get("messages", []):
                if isinstance(m.get("message"), str) and OLD in m["message"]:
                    m["message"] = m["message"].replace(OLD, NEW); count[0] += 1
            if t.get("type") == "DO_WHILE":
                replace_refs(t.get("loopOver", []), count)
            if t.get("type") == "FORK_JOIN":
                for fork in t.get("forkTasks", []):
                    replace_refs(fork, count)
        return count[0]

    replaced = replace_refs(wf["tasks"])
    print(f"mode routing: 3 cases wired, discovery_normalize in place, {replaced} refs updated")


def patch_normalize_intake(wf):
    """Ensure normalize_intake reads model/provider from workflow input, not itself."""
    for task in wf["tasks"]:
        if task.get("taskReferenceName") == "normalize_intake":
            params = task.setdefault("inputParameters", {})
            params["llm_provider"] = "${workflow.input.llm_provider}"
            params["llm_model"] = "${workflow.input.llm_model}"
            return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    wf = json.loads(P_MAIN.read_text())
    wf["version"] = VERSION
    wf["description"] = DESCRIPTION

    syn_patched = patch_synthesis_prompts(wf["tasks"])
    print(f"synthesis prompts patched: {syn_patched}")
    sal_patched = patch_salvage(wf["tasks"])
    print(f"salvage tasks patched: {sal_patched}")
    patch_tail(wf)
    print(f"tail rebuilt (exec_summary, render, sanitize, generate_pdf)")
    patch_mode_routing(wf)
    normalize_patched = patch_normalize_intake(wf)
    print(f"normalize_intake model/provider wiring patched: {normalize_patched}")

    wf["outputParameters"] = {
        "final_bundle": "${bundle_artifacts.output.result}",
        "executive_summary": "${executive_summary.output.result}",
        "markdown": "${sanitize_markdown.output.result.markdown}",
        "pdf": "${generate_pdf.output.result}",
    }

    P_MAIN.write_text(json.dumps(wf, indent=2) + "\n")
    print(f"v{wf['version']} written; tasks={len(wf['tasks'])}; outputs={list(wf['outputParameters'].keys())}")


if __name__ == "__main__":
    main()
