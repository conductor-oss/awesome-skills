#!/usr/bin/env python3
"""
gtm-mavericks eval runner.

Usage:
    runner.py --tier static
    runner.py --tier bundle --bundle <path>
    runner.py --tier all --bundle <path>
    runner.py --tier bundle --bundle <path> --no-judge

Output:
    Colored summary to stdout. Detailed JSON + markdown report in results/<timestamp>/.
    Exit code 0 if everything passes, 1 otherwise.
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent

# --- ANSI colors ---
G, Y, R, C, D, X = "\033[32m", "\033[33m", "\033[31m", "\033[36m", "\033[2m", "\033[0m"


def load_module(path: Path):
    """Load a Python file as a module without polluting sys.modules."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_test_module(path: Path, **kwargs) -> list:
    """Run a test module. Module must expose a `tests(**kwargs) -> list[dict]` function.
    Each returned dict: {name, status: pass|fail|skip, message, details?}"""
    try:
        mod = load_module(path)
    except Exception as e:
        return [{"name": f"{path.stem}:load", "status": "fail", "message": f"import error: {e}"}]

    if not hasattr(mod, "tests"):
        return [{"name": f"{path.stem}:layout", "status": "fail", "message": "missing tests() function"}]

    try:
        return mod.tests(**kwargs)
    except Exception as e:
        import traceback
        return [{"name": f"{path.stem}:exception", "status": "fail", "message": str(e), "details": traceback.format_exc()}]


def run_tier(name: str, dirpath: Path, **kwargs) -> list:
    results = []
    if not dirpath.exists():
        return results
    for f in sorted(dirpath.glob("test_*.py")):
        results.extend(run_test_module(f, **kwargs))
    return results


def print_results(tier: str, results: list):
    print(f"\n{C}── {tier} ──{X}")
    for r in results:
        status = r["status"]
        if status == "pass":
            print(f"  {G}[pass]{X} {r['name']}")
        elif status == "skip":
            print(f"  {Y}[skip]{X} {r['name']} {D}— {r.get('message','')}{X}")
        else:
            print(f"  {R}[fail]{X} {r['name']} — {r.get('message','')}")
            if r.get("details"):
                for line in r["details"].splitlines()[:8]:
                    print(f"         {D}{line}{X}")


def write_report(out_dir: Path, summary: dict, all_results: list):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps({"summary": summary, "results": all_results}, indent=2))
    md = [f"# gtm-mavericks eval report — {summary['timestamp']}", ""]
    md.append(f"**Tier:** {summary['tier']}  |  **Total:** {summary['total']}  |  "
              f"**Pass:** {summary['passed']}  |  **Fail:** {summary['failed']}  |  "
              f"**Skip:** {summary['skipped']}")
    md.append("")
    for r in all_results:
        icon = {"pass": "✅", "fail": "❌", "skip": "⏭️"}[r["status"]]
        md.append(f"- {icon} **{r['name']}** — {r.get('message','')}")
    (out_dir / "report.md").write_text("\n".join(md) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["static", "bundle", "all"], default="static")
    ap.add_argument("--bundle", type=Path, help="Path to bundle.json (required for bundle/all tier)")
    ap.add_argument("--no-judge", action="store_true", help="Skip LLM-as-judge rubrics")
    ap.add_argument("--judge-samples", type=int, default=2, help="Judge samples per rubric (default 2)")
    args = ap.parse_args()

    if args.tier in ("bundle", "all") and not args.bundle:
        print(f"{R}--bundle required for tier {args.tier}{X}", file=sys.stderr)
        sys.exit(2)
    if args.bundle and not args.bundle.exists():
        print(f"{R}Bundle not found: {args.bundle}{X}", file=sys.stderr)
        sys.exit(2)

    all_results = []

    if args.tier in ("static", "all"):
        results = run_tier("static", EVALS_DIR / "static", skill_dir=SKILL_DIR)
        print_results("static", results)
        all_results.extend(results)

    if args.tier in ("bundle", "all"):
        bundle_data = json.loads(args.bundle.read_text())
        kwargs = {
            "skill_dir": SKILL_DIR,
            "bundle": bundle_data,
            "bundle_path": args.bundle,
            "run_judge": not args.no_judge,
            "judge_samples": args.judge_samples,
        }
        results = run_tier("bundle", EVALS_DIR / "bundle", **kwargs)
        print_results("bundle", results)
        all_results.extend(results)

    total = len(all_results)
    passed = sum(1 for r in all_results if r["status"] == "pass")
    failed = sum(1 for r in all_results if r["status"] == "fail")
    skipped = sum(1 for r in all_results if r["status"] == "skip")

    color = G if failed == 0 else R
    print(f"\n{color}── Summary ──{X}")
    print(f"  Total: {total}  |  Pass: {G}{passed}{X}  |  Fail: {R}{failed}{X}  |  Skip: {Y}{skipped}{X}")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = EVALS_DIR / "results" / timestamp
    write_report(out_dir, {
        "timestamp": timestamp,
        "tier": args.tier,
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }, all_results)
    print(f"  Report: {D}{out_dir.relative_to(SKILL_DIR)}/report.{{json,md}}{X}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
