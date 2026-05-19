"""Static eval: persona library integrity."""
import re
from pathlib import Path

REQUIRED_SECTIONS = [
    "operating_principles",
    "evaluation_questions",
    "signature_moves",
    "anti_patterns",
    "voice_samples",
    "panel_contribution",
]
REQUIRED_FRONTMATTER = ["name", "era", "domain", "b2b_fit", "b2c_fit", "panel_role"]
EXPECTED_PERSONAS = {"draper", "jobs", "ogilvy", "clow", "halbert", "dunford"}


def tests(skill_dir: Path, **_):
    results = []
    personas_dir = skill_dir / "references" / "personas"

    if not personas_dir.exists():
        return [{"name": "personas:dir_exists", "status": "fail",
                 "message": f"personas dir missing: {personas_dir}"}]

    found = {p.stem for p in personas_dir.glob("*.md")}
    missing = EXPECTED_PERSONAS - found
    extra = found - EXPECTED_PERSONAS

    if missing:
        results.append({"name": "personas:roster_complete", "status": "fail",
                        "message": f"missing: {sorted(missing)}"})
    else:
        results.append({"name": "personas:roster_complete", "status": "pass",
                        "message": f"all 6 personas present"})

    if extra:
        results.append({"name": "personas:no_unexpected", "status": "fail",
                        "message": f"unexpected files: {sorted(extra)}"})
    else:
        results.append({"name": "personas:no_unexpected", "status": "pass", "message": ""})

    # Per-persona checks
    try:
        import yaml
    except ImportError:
        results.append({"name": "personas:yaml_parse", "status": "skip",
                        "message": "pyyaml not installed; pip install pyyaml"})
        return results

    for persona in sorted(EXPECTED_PERSONAS & found):
        path = personas_dir / f"{persona}.md"
        content = path.read_text()

        # Frontmatter
        parts = content.split("---", 2)
        if len(parts) != 3:
            results.append({"name": f"personas:{persona}:frontmatter",
                            "status": "fail", "message": "malformed frontmatter delimiters"})
            continue
        try:
            data = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            results.append({"name": f"personas:{persona}:frontmatter",
                            "status": "fail", "message": f"yaml error: {e}"})
            continue

        missing_keys = [k for k in REQUIRED_FRONTMATTER if k not in data]
        if missing_keys:
            results.append({"name": f"personas:{persona}:frontmatter",
                            "status": "fail",
                            "message": f"missing frontmatter keys: {missing_keys}"})
        else:
            results.append({"name": f"personas:{persona}:frontmatter",
                            "status": "pass", "message": ""})

        # Body sections
        body = parts[2]
        missing_sections = [s for s in REQUIRED_SECTIONS
                            if not re.search(rf"^##\s+{re.escape(s)}\b", body, re.MULTILINE)]
        if missing_sections:
            results.append({"name": f"personas:{persona}:sections",
                            "status": "fail",
                            "message": f"missing sections: {missing_sections}"})
        else:
            results.append({"name": f"personas:{persona}:sections",
                            "status": "pass", "message": ""})

        # Substance check — each section should have at least one bullet/line of content
        for section in REQUIRED_SECTIONS:
            m = re.search(rf"^##\s+{re.escape(section)}\b(.*?)(?=^##\s|\Z)",
                          body, re.MULTILINE | re.DOTALL)
            if m:
                section_text = m.group(1).strip()
                non_blank = [l for l in section_text.splitlines() if l.strip()]
                if len(non_blank) < 2:
                    results.append({"name": f"personas:{persona}:{section}:substance",
                                    "status": "fail",
                                    "message": f"section has {len(non_blank)} non-blank lines, expected ≥2"})

    return results
