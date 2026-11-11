# DSC 190 Assignment 07: Reproducible Data Pipelines

Run commands from the repository root with Python 3.12+ and uv installed:

```sh
uv sync --locked
uv run dvc repro
uv run python -m unittest discover -s tests -v
uv run marimo edit notebooks/report.py
```

The dependencies (`dvc`, `pandas`, `marimo`, and `matplotlib`) are declared in
`pyproject.toml` and pinned transitively in `uv.lock`. Tests use standard-library
`unittest` and require no additional dependency.

`dvc.yaml` defines this dependency chain:

```text
data/raw/events.csv
  -> clean     (scripts/clean.py)     -> data/clean/events.csv
  -> transform (scripts/transform.py) -> data/transformed/events.csv
  -> features  (scripts/features.py)  -> data/features/events.csv
```

Each stage tracks its script, input CSV, project manifest, and dependency lockfile.
`dvc.lock` records the resulting dependency/output hashes. The raw file is read
only; row order and duplicates are retained. Transform adds `date`; features adds
`duration_minutes` and the full English `weekday`, preserving input rows and columns.
The Marimo report reads the feature file and displays a matplotlib histogram.
Run the pipeline before opening the notebook.

## Validation rules and assumptions

Inspection of the 2,000 raw records found five frequent canonical event values:
`click` (395), `login` (384), `purchase` (366), `scroll` (350), and `view` (348).
These form a fixed, case-sensitive allowlist. Less common values (`PURCHASE!`,
`test`, `VIEW`, `klick`, `log_in`, `buy`, `unknown`) are treated as invalid,
not mapped to canonical values. This is an inferred vocabulary, not an externally
provided schema; new valid types require an explicit rule update.

Rows with null, empty, or whitespace-only fields are removed. Durations must be
positive integer strings (an optional leading `+` is accepted), representable as
signed 64-bit integers; fractions, nonnumeric values, zero, and negatives are
rejected. Output durations have integer dtype.

Accepted timestamp formats, based on the source, are `YYYY-MM-DDTHH:MM:SS`,
`YYYY-MM-DDTHH:MM:SS.fraction`, `YYYY-MM-DD HH:MM:SS`, and
`MM/DD/YYYY HH:MM:SS`. Dates must be calendar-valid. Slash dates use US month-first
order. Timestamps are timezone-naive; no timezone conversion is inferred.
Fractional seconds are truncated to normalize to `YYYY-MM-DDTHH:MM:SS`.
Empty valid results still produce CSV headers.

## Reproduction checks

```sh
uv run python tests/verify_repro.py
uv run dvc status
uv run marimo check notebooks/report.py
uv run marimo export html notebooks/report.py -o /tmp/events-report.html
```

`verify_repro.py` checks output schemas and values, deletes only the three derived
CSV files, and verifies DVC restores them from cache. It then backs up the local
`.dvc/cache`, removes it and the derived CSVs, rebuilds all stages, and restores
the original cache in a `finally` block. Both runs must reproduce byte-identical
CSVs and preserve the raw file's SHA-256. This check assumes the default local
DVC cache location and must run without another DVC process using the repository.
No remote cache is required.

Validated result: 2,000 raw rows become 1,612 rows in each derived CSV (388 rows
removed). All five unit tests, CSV invariants, warm-cache restoration, cold-cache
rebuilding, and raw-file integrity checks pass.

Git ignores `.venv`, Python caches, Marimo state, and generated pipeline outputs;
`.dvc/.gitignore` excludes DVC's local cache and state. Keep `dvc.yaml`, `dvc.lock`,
`uv.lock`, scripts, tests, notebook, and DVC initialization metadata in version
control. No commit or push is performed by these instructions.

In restricted environments, redirect machine-level caches to writable paths:

```sh
export UV_CACHE_DIR=/tmp/dsc190-uv-cache
export DVC_SITE_CACHE_DIR=/tmp/dsc190-dvc-site
export MPLCONFIGDIR=/tmp/dsc190-matplotlib
```

The Marimo export starts a local kernel socket, so it requires an environment
that permits local socket binding.
