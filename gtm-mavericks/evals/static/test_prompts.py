"""Static eval: every prompt referenced by the workflow exists in prompt-templates/."""
import json
import re
from pathlib import Path


def tests(skill_dir: Path, **_):
    results = []
    prompts_dir = skill_dir / "references" / "prompt-templates"
    wf_dir = skill_dir / "references" / "workflow-definitions"

    if not prompts_dir.exists():
        return [{"name": "prompts:dir_exists", "status": "fail",
                 "message": f"prompts dir missing: {prompts_dir}"}]

    # Collect every "prompt": "<name>" reference from workflow JSONs
    referenced = set()
    for wf_file in wf_dir.glob("*.json"):
        text = wf_file.read_text()
        # Match "prompt": "<value>" — captures any string value
        for m in re.finditer(r'"prompt"\s*:\s*"([^"]+)"', text):
            referenced.add(m.group(1))

    # Available prompt files (without extension)
    available = {p.stem for p in prompts_dir.glob("*.md")} | \
                {p.stem for p in prompts_dir.glob("*.txt")}

    # Note: many workflows now use allowRawPrompts:true with inlined prompts,
    # in which case the "prompt" key may not appear at all. That's fine.
    if not referenced:
        results.append({"name": "prompts:referenced_by_workflows",
                        "status": "pass",
                        "message": f"no external prompt references (inlined via allowRawPrompts)"})
    else:
        missing = referenced - available
        if missing:
            results.append({"name": "prompts:all_referenced_exist",
                            "status": "fail",
                            "message": f"workflow references missing prompts: {sorted(missing)}"})
        else:
            results.append({"name": "prompts:all_referenced_exist",
                            "status": "pass",
                            "message": f"{len(referenced)} prompt(s) referenced, all present"})

    # Spot-check that essential prompts exist on disk (even if inlined in workflow,
    # they should still be available for reference)
    essentials = ["persona-panel-critique", "icp-synthesis",
                  "positioning-synthesis", "messaging-house"]
    for name in essentials:
        if any((prompts_dir / f"{name}.{ext}").exists() for ext in ("md", "txt")):
            results.append({"name": f"prompts:essential:{name}", "status": "pass",
                            "message": ""})
        else:
            results.append({"name": f"prompts:essential:{name}", "status": "fail",
                            "message": f"missing {name}.md or {name}.txt"})

    return results
