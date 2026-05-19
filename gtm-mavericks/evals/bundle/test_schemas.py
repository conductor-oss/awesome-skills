"""Bundle eval: each artifact in the bundle validates against its JSON Schema."""
import json
from pathlib import Path


def _validate(instance, schema):
    """Minimal JSON Schema validator covering the subset our schemas use.
    Supports: type (object/array/string/number/boolean), required, properties,
    items, minItems, enum, oneOf. Returns (ok, errors)."""
    errors = []

    def walk(inst, sch, path="$"):
        # oneOf: instance must validate against exactly one branch
        if "oneOf" in sch:
            branch_errors = []
            matches = 0
            for i, branch in enumerate(sch["oneOf"]):
                _, branch_errs = _validate(inst, branch)
                if not branch_errs:
                    matches += 1
                else:
                    branch_errors.append((i, branch_errs))
            if matches != 1:
                if matches == 0:
                    errors.append(f"{path}: matched no oneOf branches; tried {len(sch['oneOf'])} ({type(inst).__name__})")
                else:
                    errors.append(f"{path}: matched {matches} oneOf branches; expected exactly 1")
            return

        t = sch.get("type")
        if t == "object":
            if not isinstance(inst, dict):
                errors.append(f"{path}: expected object, got {type(inst).__name__}")
                return
            for required in sch.get("required", []):
                if required not in inst:
                    errors.append(f"{path}: missing required field '{required}'")
            for key, prop_schema in sch.get("properties", {}).items():
                if key in inst:
                    walk(inst[key], prop_schema, f"{path}.{key}")
        elif t == "array":
            if not isinstance(inst, list):
                errors.append(f"{path}: expected array, got {type(inst).__name__}")
                return
            min_items = sch.get("minItems", 0)
            if len(inst) < min_items:
                errors.append(f"{path}: array length {len(inst)} < minItems {min_items}")
            if "items" in sch:
                for i, item in enumerate(inst):
                    walk(item, sch["items"], f"{path}[{i}]")
        elif t == "string":
            if not isinstance(inst, str):
                if inst is not None:
                    errors.append(f"{path}: expected string, got {type(inst).__name__}")
        elif t == "number":
            if not isinstance(inst, (int, float)):
                errors.append(f"{path}: expected number, got {type(inst).__name__}")
        elif t == "boolean":
            if not isinstance(inst, bool):
                errors.append(f"{path}: expected boolean, got {type(inst).__name__}")
        elif "enum" in sch:
            if inst not in sch["enum"]:
                errors.append(f"{path}: {inst!r} not in enum {sch['enum']}")

    walk(instance, schema)
    return (len(errors) == 0, errors)


def tests(skill_dir: Path, bundle: dict, **_):
    results = []
    schema_dir = skill_dir / "references" / "artifact-schemas"

    # Map bundle field → schema file
    mapping = [
        ("icp_one_pager", "icp-one-pager.schema.json"),
        ("positioning", "positioning-synthesis.schema.json"),
        ("messaging_house", "messaging-house.schema.json"),
    ]

    for field, schema_file in mapping:
        schema_path = schema_dir / schema_file
        if not schema_path.exists():
            results.append({"name": f"schema:{field}:schema_exists",
                            "status": "skip",
                            "message": f"schema file missing: {schema_file}"})
            continue

        if field not in bundle:
            results.append({"name": f"schema:{field}:present",
                            "status": "fail",
                            "message": f"bundle missing {field}"})
            continue

        schema = json.loads(schema_path.read_text())
        ok, errs = _validate(bundle[field], schema)
        if ok:
            results.append({"name": f"schema:{field}:validates", "status": "pass", "message": ""})
        else:
            results.append({"name": f"schema:{field}:validates",
                            "status": "fail",
                            "message": f"{len(errs)} validation error(s)",
                            "details": "\n".join(errs[:6])})

    # Artifacts (array of asset artifacts)
    if "artifacts" in bundle:
        asset_schema_path = schema_dir / "asset-artifact.schema.json"
        if asset_schema_path.exists():
            schema = json.loads(asset_schema_path.read_text())
            artifact_errors = []
            for i, artifact in enumerate(bundle["artifacts"]):
                ok, errs = _validate(artifact, schema)
                if not ok:
                    artifact_errors.append(f"artifact[{i}]: {errs[0]}")
            if not artifact_errors:
                results.append({"name": "schema:artifacts:validate",
                                "status": "pass",
                                "message": f"{len(bundle['artifacts'])} artifact(s) valid"})
            else:
                results.append({"name": "schema:artifacts:validate",
                                "status": "fail",
                                "message": f"{len(artifact_errors)} artifact(s) failed",
                                "details": "\n".join(artifact_errors[:6])})

    return results
