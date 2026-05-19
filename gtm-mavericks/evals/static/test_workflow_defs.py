"""Static eval: workflow definition validity + structural rules."""
import json
from pathlib import Path

EXPECTED_WORKFLOWS = {
    "gtm_mavericks_v1.json": "gtm_mavericks_v1",
    "discovery_new_product.json": "discovery_new_product",
    "discovery_reposition.json": "discovery_reposition",
    "discovery_campaign.json": "discovery_campaign",
}


def find_tasks_recursive(tasks):
    """Walk the task tree including FORK_JOIN.forkTasks and SWITCH.decisionCases."""
    for t in tasks or []:
        yield t
        if t.get("type") == "FORK_JOIN":
            for branch in t.get("forkTasks", []):
                yield from find_tasks_recursive(branch)
        elif t.get("type") == "SWITCH":
            for case_tasks in (t.get("decisionCases") or {}).values():
                yield from find_tasks_recursive(case_tasks)
            yield from find_tasks_recursive(t.get("defaultCase", []))


def tests(skill_dir: Path, **_):
    results = []
    wf_dir = skill_dir / "references" / "workflow-definitions"

    if not wf_dir.exists():
        return [{"name": "workflows:dir_exists", "status": "fail",
                 "message": f"workflow dir missing: {wf_dir}"}]

    for filename, expected_name in EXPECTED_WORKFLOWS.items():
        path = wf_dir / filename
        if not path.exists():
            results.append({"name": f"workflows:{filename}:exists", "status": "fail",
                            "message": "file missing"})
            continue

        try:
            wf = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            results.append({"name": f"workflows:{filename}:parses", "status": "fail",
                            "message": f"JSON parse error: {e}"})
            continue

        results.append({"name": f"workflows:{filename}:parses", "status": "pass", "message": ""})

        if wf.get("name") != expected_name:
            results.append({"name": f"workflows:{filename}:name",
                            "status": "fail",
                            "message": f"name={wf.get('name')!r}, expected {expected_name!r}"})

        if "tasks" not in wf or not isinstance(wf["tasks"], list) or not wf["tasks"]:
            results.append({"name": f"workflows:{filename}:tasks",
                            "status": "fail", "message": "no tasks array"})
            continue

    # Structural rules on the main workflow
    main_path = wf_dir / "gtm_mavericks_v1.json"
    if main_path.exists():
        try:
            main = json.loads(main_path.read_text())
        except Exception:
            return results

        all_tasks = list(find_tasks_recursive(main["tasks"]))
        task_names = [t.get("name", "") for t in all_tasks]
        task_refs = [t.get("taskReferenceName", "") for t in all_tasks]

        # Has the 4 gate names (whether INLINE or HUMAN)
        expected_gates = ["gate_icp_review", "gate_positioning_review",
                          "gate_pick_asset_voice", "gate_final_review"]
        found_gates = [g for g in expected_gates if g in task_refs]
        if len(found_gates) == 4:
            results.append({"name": "workflows:main:has_4_gates", "status": "pass",
                            "message": "all 4 gate refs present"})
        else:
            results.append({"name": "workflows:main:has_4_gates", "status": "fail",
                            "message": f"found gates: {found_gates}, expected: {expected_gates}"})

        # Has a panel for ICP and positioning
        for panel in ("icp_panel", "positioning_panel"):
            if panel in task_refs:
                results.append({"name": f"workflows:main:{panel}_exists",
                                "status": "pass", "message": ""})
            else:
                results.append({"name": f"workflows:main:{panel}_exists",
                                "status": "fail",
                                "message": f"missing {panel} task ref"})

        # Has the 3 mode-routed sub-workflows referenced
        decision_cases = []
        for t in all_tasks:
            if t.get("type") == "SWITCH":
                decision_cases.extend((t.get("decisionCases") or {}).keys())
        expected_modes = {"new_product", "reposition", "campaign"}
        found_modes = set(decision_cases)
        if expected_modes <= found_modes:
            results.append({"name": "workflows:main:mode_router_complete",
                            "status": "pass",
                            "message": f"all 3 modes routed: {sorted(found_modes & expected_modes)}"})
        else:
            results.append({"name": "workflows:main:mode_router_complete",
                            "status": "fail",
                            "message": f"missing mode cases: {sorted(expected_modes - found_modes)}"})

    return results
