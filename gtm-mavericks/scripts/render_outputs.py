"""Pull a completed GTM Mavericks workflow's outputs (markdown + PDF) to disk.

The workflow renders its own markdown and PDF inside Conductor (via INLINE
render_markdown + GENERATE_PDF tasks). This script just fetches them and writes them
out, plus the structured JSON bundles for downstream tooling.

Usage:
    python3 render_outputs.py <workflow_id> [<output_dir>]
    python3 render_outputs.py --run-id <run_id>   # reads .gtm/runs/<run-id>/state.json

Env:
    CONDUCTOR_SERVER_URL                                (e.g. http://localhost:8080/api)
    Optional auth: CONDUCTOR_AUTH_KEY + CONDUCTOR_AUTH_SECRET, or CONDUCTOR_PROFILE.
                   OSS Conductor on /api typically needs no auth.
"""
import json
import os
import pathlib
import shutil
import sys
import urllib.parse
import urllib.request


def get_auth():
    server = os.environ.get("CONDUCTOR_SERVER_URL")
    if not server:
        sys.exit("CONDUCTOR_SERVER_URL not set")
    key = os.environ.get("CONDUCTOR_AUTH_KEY")
    secret = os.environ.get("CONDUCTOR_AUTH_SECRET")
    if not (key and secret):
        profile = os.environ.get("CONDUCTOR_PROFILE")
        if profile:
            cfg = pathlib.Path.home() / ".conductor-cli" / f"config-{profile}.yaml"
            if cfg.exists():
                for line in cfg.read_text().splitlines():
                    if line.startswith("auth-key:"):
                        key = line.split(":", 1)[1].strip()
                    elif line.startswith("auth-secret:"):
                        secret = line.split(":", 1)[1].strip()
    if not (key and secret):
        return None, server
    req = urllib.request.Request(
        f"{server}/token",
        data=json.dumps({"keyId": key, "keySecret": secret}).encode(),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["token"], server


def fetch_workflow(workflow_id, token, server):
    req = urllib.request.Request(f"{server}/workflow/{workflow_id}?includeTasks=true")
    if token:
        req.add_header("X-Authorization", token)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: render_outputs.py <workflow_id> [<output_dir>]\n   or: render_outputs.py --run-id <run_id>")

    if sys.argv[1] == "--run-id":
        run_id = sys.argv[2]
        state_path = pathlib.Path.cwd() / ".gtm" / "runs" / run_id / "state.json"
        if not state_path.exists():
            sys.exit(f"state.json not found at {state_path}")
        state = json.loads(state_path.read_text())
        workflow_id = state.get("workflowId")
        out_dir = pathlib.Path.cwd() / "gtm-output" / run_id
    else:
        workflow_id = sys.argv[1]
        out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) >= 3 else pathlib.Path.cwd() / f"gtm-output-{workflow_id[:8]}"

    out_dir.mkdir(parents=True, exist_ok=True)
    token, server = get_auth()
    print(f"fetching workflow {workflow_id}...")
    wf = fetch_workflow(workflow_id, token, server)
    status = wf.get("status")
    if status != "COMPLETED":
        print(f"  warning: workflow status is {status}, not COMPLETED -- output may be partial")

    output = wf.get("output", {})
    if not output:
        sys.exit("workflow has no top-level output -- has it finalized?")

    bundle = output.get("final_bundle", {})
    if bundle:
        (out_dir / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n")
        print(f"  bundle.json ({len(json.dumps(bundle))} chars; keys: {list(bundle.keys())})")

    summary = output.get("executive_summary", {})
    if summary:
        (out_dir / "executive_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(f"  executive_summary.json (keys: {list(summary.keys())})")

    md = output.get("markdown", "")
    if md:
        md_path = out_dir / "gtm-full.md"
        md_path.write_text(md)
        print(f"  gtm-full.md ({len(md)} chars)")

    pdf = output.get("pdf")
    if isinstance(pdf, dict) and pdf.get("location"):
        loc = pdf["location"]
        if loc.startswith("file://"):
            src = urllib.parse.unquote(loc[7:])
            dst = out_dir / "gtm-full.pdf"
            try:
                shutil.copy(src, dst)
                print(f"  gtm-full.pdf ({dst.stat().st_size} bytes)")
            except Exception as e:
                print(f"  pdf copy failed: {e} (source: {src})")
        else:
            print(f"  pdf at remote location: {loc}")

    print(f"\nDone. Output in: {out_dir}")


if __name__ == "__main__":
    main()
