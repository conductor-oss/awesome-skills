# Bundle fixtures

Drop captured `bundle.json` files here to use as deterministic test fixtures.

## Capturing a fixture

After a successful workflow run:

```bash
cp /path/to/.gtm/runs/<run-id>/bundle.json \
   evals/bundle/fixtures/<descriptive-name>.bundle.json
```

Naming convention: `<mode>_<short-product-name>.bundle.json` — e.g., `mode_b_hublink_reposition.bundle.json`.

## Running evals against a fixture

```bash
python3 evals/runner.py --tier bundle \
    --bundle evals/bundle/fixtures/<your-fixture>.bundle.json
```

## What to capture

Aim for one fixture per mode (A, B, C). Pick runs that you'd want to lock in as "this is at least the quality bar we hit on date X." When a regression drops scores below a fixture's baseline, you'll see it in the eval report.

## Sensitive content

Bundles contain product names, ICPs, and positioning the run was for. If a fixture is from a real customer or partner, do NOT commit it. Add a line to `.gitignore`:

```
evals/bundle/fixtures/*.bundle.json
!evals/bundle/fixtures/example.bundle.json
```

…and keep one safe example fixture in version control.
