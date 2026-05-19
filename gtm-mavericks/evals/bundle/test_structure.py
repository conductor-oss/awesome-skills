"""Bundle eval: structural rules beyond schema (counts, presence, basic quality)."""
from pathlib import Path


def tests(skill_dir: Path, bundle: dict, **_):
    results = []

    # --- ICP ---
    icp = bundle.get("icp_one_pager") or {}
    primary = icp.get("primary_icp") or {}
    required_fields = ["demographic", "psychographic", "trigger_event",
                       "current_alternative", "pain_in_their_words"]

    missing = [f for f in required_fields if not primary.get(f)]
    if missing:
        results.append({"name": "structure:icp:complete_primary",
                        "status": "fail",
                        "message": f"primary ICP missing/empty: {missing}"})
    else:
        results.append({"name": "structure:icp:complete_primary",
                        "status": "pass", "message": ""})

    # ICP demographic should be specific — penalize very short ones
    demo = primary.get("demographic", "")
    if isinstance(demo, str) and len(demo) < 40:
        results.append({"name": "structure:icp:demographic_specificity",
                        "status": "fail",
                        "message": f"demographic only {len(demo)} chars — likely vague"})
    elif demo:
        results.append({"name": "structure:icp:demographic_specificity",
                        "status": "pass", "message": f"{len(demo)} chars"})

    # --- Positioning ---
    pos = bundle.get("positioning") or {}
    forks = pos.get("strategic_forks") or []
    if len(forks) >= 1:
        results.append({"name": "structure:positioning:has_forks",
                        "status": "pass",
                        "message": f"{len(forks)} strategic fork(s)"})
    else:
        results.append({"name": "structure:positioning:has_forks",
                        "status": "fail",
                        "message": "no strategic forks — panel didn't disagree"})

    rec_pos = pos.get("recommended_positioning") or {}
    pos_fields = ["for", "who_struggles_with", "our_product", "is_a", "that", "unlike"]
    missing_pos = [f for f in pos_fields if not rec_pos.get(f)]
    if missing_pos:
        results.append({"name": "structure:positioning:complete_statement",
                        "status": "fail",
                        "message": f"recommended_positioning missing: {missing_pos}"})
    else:
        results.append({"name": "structure:positioning:complete_statement",
                        "status": "pass", "message": ""})

    cat = (pos.get("category_design") or {}).get("category_name") or ""
    if cat:
        results.append({"name": "structure:positioning:has_category",
                        "status": "pass", "message": cat[:60]})
    else:
        results.append({"name": "structure:positioning:has_category",
                        "status": "fail",
                        "message": "no category_name — half the positioning value is missing"})

    # --- Messaging house ---
    mh = bundle.get("messaging_house") or {}
    pillars = mh.get("proof_pillars") or []
    if len(pillars) >= 3:
        results.append({"name": "structure:messaging_house:pillars",
                        "status": "pass",
                        "message": f"{len(pillars)} proof pillars"})
    else:
        results.append({"name": "structure:messaging_house:pillars",
                        "status": "fail",
                        "message": f"only {len(pillars)} pillars — expected ≥3"})

    # Anti-messaging is the half most teams skip — must have entries
    anti = mh.get("anti_messaging") or []
    if len(anti) >= 2:
        results.append({"name": "structure:messaging_house:anti_messaging",
                        "status": "pass",
                        "message": f"{len(anti)} anti-messaging entries"})
    else:
        results.append({"name": "structure:messaging_house:anti_messaging",
                        "status": "fail",
                        "message": f"only {len(anti)} anti-messaging entries — expected ≥2"})

    # Pillars should have evidence
    pillars_without_evidence = sum(1 for p in pillars
                                    if not (p.get("evidence") or "").strip())
    if pillars_without_evidence == 0 and pillars:
        results.append({"name": "structure:messaging_house:pillars_have_evidence",
                        "status": "pass", "message": ""})
    elif pillars:
        results.append({"name": "structure:messaging_house:pillars_have_evidence",
                        "status": "fail",
                        "message": f"{pillars_without_evidence}/{len(pillars)} pillars missing evidence"})

    # --- Artifacts ---
    artifacts = bundle.get("artifacts") or []
    if len(artifacts) >= 1:
        results.append({"name": "structure:artifacts:present",
                        "status": "pass", "message": f"{len(artifacts)} artifact(s)"})
    else:
        results.append({"name": "structure:artifacts:present",
                        "status": "fail",
                        "message": "no artifacts in bundle"})

    # Every artifact records its voice_persona
    voiced = sum(1 for a in artifacts if a.get("voice_persona"))
    if artifacts and voiced == len(artifacts):
        results.append({"name": "structure:artifacts:voice_persona_recorded",
                        "status": "pass", "message": ""})
    elif artifacts:
        results.append({"name": "structure:artifacts:voice_persona_recorded",
                        "status": "fail",
                        "message": f"{len(artifacts) - voiced}/{len(artifacts)} artifacts missing voice_persona"})

    # --- Top-level bundle metadata ---
    for field in ("mode", "run_id"):
        if bundle.get(field):
            results.append({"name": f"structure:bundle:{field}",
                            "status": "pass", "message": str(bundle[field])[:40]})
        else:
            results.append({"name": f"structure:bundle:{field}",
                            "status": "fail",
                            "message": f"bundle missing top-level {field}"})

    return results
