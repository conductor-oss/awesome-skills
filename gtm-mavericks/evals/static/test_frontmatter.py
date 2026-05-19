"""Static eval: SKILL.md frontmatter is valid Claude Code frontmatter."""
from pathlib import Path


REQUIRED_KEYS = ["name", "description"]
RECOMMENDED_KEYS = ["allowed-tools"]


def tests(skill_dir: Path, **_):
    results = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return [{"name": "frontmatter:skill_md_exists", "status": "fail",
                 "message": "SKILL.md not found"}]

    try:
        import yaml
    except ImportError:
        return [{"name": "frontmatter:yaml_available", "status": "skip",
                 "message": "pyyaml not installed"}]

    content = skill_md.read_text()
    if not content.startswith("---"):
        return [{"name": "frontmatter:has_delimiters", "status": "fail",
                 "message": "SKILL.md doesn't start with ---"}]

    parts = content.split("---", 2)
    if len(parts) < 3:
        return [{"name": "frontmatter:has_delimiters", "status": "fail",
                 "message": "frontmatter delimiters malformed"}]

    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return [{"name": "frontmatter:parses", "status": "fail",
                 "message": f"YAML error: {e}"}]

    results.append({"name": "frontmatter:parses", "status": "pass", "message": ""})

    for key in REQUIRED_KEYS:
        if key in data:
            results.append({"name": f"frontmatter:has_{key}", "status": "pass", "message": ""})
        else:
            results.append({"name": f"frontmatter:has_{key}", "status": "fail",
                            "message": f"missing required key: {key}"})

    # Description should be substantive (Claude Code uses it for skill discovery)
    desc = data.get("description", "")
    if len(desc) < 80:
        results.append({"name": "frontmatter:description_substance",
                        "status": "fail",
                        "message": f"description is {len(desc)} chars; ≥80 expected for good skill discovery"})
    else:
        results.append({"name": "frontmatter:description_substance",
                        "status": "pass",
                        "message": f"{len(desc)} chars"})

    # Description should mention when to use the skill
    if any(phrase in desc.lower() for phrase in ["use when", "use this", "for ", "run "]):
        results.append({"name": "frontmatter:description_use_signal",
                        "status": "pass",
                        "message": "describes when to invoke"})
    else:
        results.append({"name": "frontmatter:description_use_signal",
                        "status": "fail",
                        "message": "description should include 'use when' or similar trigger signal"})

    for key in RECOMMENDED_KEYS:
        if key in data:
            results.append({"name": f"frontmatter:has_{key}", "status": "pass", "message": ""})
        else:
            results.append({"name": f"frontmatter:has_{key}", "status": "skip",
                            "message": f"recommended key missing: {key} (Claude Code-specific)"})

    return results
