"""LLM-as-judge harness. Auto-discovers rubrics in ./rubrics/ and grades the bundle.

Each rubric is a markdown file with two sections:
- ## Inputs — what bundle fields the rubric needs
- ## Rubric — the grading rubric (criteria, pass condition, examples)

The judge LLM (Anthropic claude-haiku-4-5) reads the relevant bundle fields + rubric,
returns JSON {score: 1-5, reasoning: ...}. We sample N times per rubric and average.

Skipped gracefully if ANTHROPIC_API_KEY is not set.
"""
import json
import os
from pathlib import Path


def _anthropic_available():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, "ANTHROPIC_API_KEY not set"
    try:
        import anthropic  # noqa
        return True, None
    except ImportError:
        return False, "anthropic SDK not installed (pip install anthropic)"


def _grade(rubric_text: str, bundle_excerpt: dict, model: str = "claude-haiku-4-5-20251001"):
    """Call the judge model via tool_use to guarantee structured output.
    Returns {score, reasoning}."""
    import anthropic
    client = anthropic.Anthropic()

    system = """You are grading the output of a go-to-market strategy workflow against a specific rubric.
Be rigorous and honest. Score 1 (utter failure) to 5 (exceptional).
A 3 means "acceptable but not great." Most professional output should score 3-4.
Call the `submit_grade` tool exactly once with your score and reasoning."""

    user = f"""# Rubric

{rubric_text}

# Bundle output to grade

```json
{json.dumps(bundle_excerpt, indent=2)[:8000]}
```

Grade strictly per the rubric. Call submit_grade with your score (1-5) and a one-paragraph reasoning."""

    tools = [{
        "name": "submit_grade",
        "description": "Submit the final grade for the bundle against the rubric.",
        "input_schema": {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "minimum": 1, "maximum": 5,
                          "description": "Integer 1-5"},
                "reasoning": {"type": "string",
                              "description": "One-paragraph rationale, citing rubric criteria"},
            },
            "required": ["score", "reasoning"],
        },
    }]

    resp = client.messages.create(
        model=model,
        max_tokens=800,
        system=system,
        tools=tools,
        tool_choice={"type": "tool", "name": "submit_grade"},
        messages=[{"role": "user", "content": user}],
    )
    # The response will contain a tool_use block with our structured input
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "submit_grade":
            return block.input
    raise ValueError("judge did not call submit_grade tool")


def tests(skill_dir: Path, bundle: dict, run_judge: bool = True,
          judge_samples: int = 2, **_):
    results = []
    rubrics_dir = Path(__file__).parent / "rubrics"

    if not run_judge:
        results.append({"name": "judge:disabled", "status": "skip",
                        "message": "--no-judge specified"})
        return results

    ok, reason = _anthropic_available()
    if not ok:
        results.append({"name": "judge:setup", "status": "skip",
                        "message": reason})
        return results

    if not rubrics_dir.exists():
        return [{"name": "judge:rubrics_dir", "status": "fail",
                 "message": f"rubrics dir missing: {rubrics_dir}"}]

    rubrics = sorted(rubrics_dir.glob("*.md"))
    if not rubrics:
        return [{"name": "judge:no_rubrics", "status": "fail",
                 "message": "no rubric .md files found"}]

    for rubric_path in rubrics:
        rubric_name = rubric_path.stem
        rubric_text = rubric_path.read_text()

        # Per-rubric input selection — keeps the prompt small
        excerpt = _select_excerpt(rubric_name, bundle)

        scores = []
        errors = []
        for i in range(judge_samples):
            try:
                result = _grade(rubric_text, excerpt)
                scores.append(int(result["score"]))
            except Exception as e:
                errors.append(f"sample {i+1}: {e}")

        if not scores:
            results.append({"name": f"judge:{rubric_name}", "status": "fail",
                            "message": "no successful samples",
                            "details": "\n".join(errors)})
            continue

        mean = sum(scores) / len(scores)
        passed = mean >= 3.5
        status = "pass" if passed else "fail"
        results.append({
            "name": f"judge:{rubric_name}",
            "status": status,
            "message": f"mean score {mean:.2f}/5 across {len(scores)} sample(s) — scores: {scores}",
        })

    return results


def _select_excerpt(rubric_name: str, bundle: dict) -> dict:
    """Pick only the bundle fields each rubric needs.

    Critically: the icp rubric must see ONLY primary_icp — not secondary_icps
    or rejected_candidates, which the judge would otherwise pick at random
    and grade the weakest one.
    """
    if "icp" in rubric_name:
        icp = bundle.get("icp_one_pager") or {}
        return {
            "primary_icp": icp.get("primary_icp"),
            "_context_only_panel_disagreements_count":
                len(icp.get("panel_disagreements") or []),
        }
    if "positioning" in rubric_name:
        pos = bundle.get("positioning") or {}
        return {
            "recommended_positioning": pos.get("recommended_positioning"),
            "strategic_forks": pos.get("strategic_forks"),
            "category_design": pos.get("category_design"),
        }
    if "persona_voice" in rubric_name:
        artifacts = bundle.get("artifacts") or []
        specific = [a for a in artifacts
                    if a.get("voice_persona") in
                    {"draper", "jobs", "ogilvy", "clow", "halbert", "dunford"}]
        return {
            "artifacts": specific[:2] if specific else artifacts[:2],
            "voice_personas_present": sorted({
                a.get("voice_persona") for a in artifacts
                if a.get("voice_persona")
            }),
            "all_artifacts_were_composed": len(specific) == 0 and len(artifacts) > 0,
        }
    if "anti_messaging" in rubric_name:
        mh = bundle.get("messaging_house") or {}
        return {
            "anti_messaging": mh.get("anti_messaging"),
            "_context_north_star": mh.get("north_star"),
            "_context_taglines": mh.get("taglines"),
        }
    return bundle
