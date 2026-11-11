"""Destructive only to derived outputs/cache; run from repository root."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pandas as pd
from pandas.testing import assert_frame_equal


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    raw = Path("data/raw/events.csv")
    raw_hash = digest(raw)
    outputs = [Path(f"data/{stage}/events.csv") for stage in ("clean", "transformed", "features")]
    expected = {path: digest(path) for path in outputs}
    clean, transformed, features = [pd.read_csv(path) for path in outputs]
    assert clean.notna().all().all()
    assert (clean.duration_seconds > 0).all()
    assert pd.api.types.is_integer_dtype(clean.duration_seconds)
    assert clean.timestamp.str.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}").all()
    assert_frame_equal(clean, transformed[clean.columns])
    assert_frame_equal(transformed, features[transformed.columns])
    dates = pd.to_datetime(clean.timestamp, format="%Y-%m-%dT%H:%M:%S")
    assert transformed.date.tolist() == dates.dt.strftime("%Y-%m-%d").tolist()
    assert features.weekday.tolist() == dates.dt.day_name().tolist()
    assert ((features.duration_minutes - clean.duration_seconds / 60).abs() < 1e-12).all()
    env = dict(os.environ, UV_CACHE_DIR=os.environ.get("UV_CACHE_DIR", "/tmp/dsc190-uv-cache"), DVC_SITE_CACHE_DIR=os.environ.get("DVC_SITE_CACHE_DIR", "/tmp/dsc190-dvc-site"))
    def dvc(*args):
        subprocess.run(["uv", "run", "dvc", *args], check=True, env=env)
    # Verify restoration from existing cache first.
    for path in outputs:
        path.unlink()
    dvc("repro")
    assert {path: digest(path) for path in outputs} == expected
    # Preserve and restore the original cache even if cold rebuilding fails.
    cache = Path(".dvc/cache")
    with tempfile.TemporaryDirectory(prefix="dsc190-cache-") as temp:
        backup = Path(temp) / "cache"
        shutil.copytree(cache, backup)
        try:
            shutil.rmtree(cache)
            for path in outputs:
                path.unlink()
            dvc("repro")
            assert {path: digest(path) for path in outputs} == expected
        finally:
            if cache.exists():
                shutil.rmtree(cache)
            shutil.copytree(backup, cache)
    dvc("status")
    assert digest(raw) == raw_hash
    print(f"Verified {len(pd.read_csv(raw))} raw rows -> {len(clean)} clean/transformed/feature rows.")
    print("CSV invariants, warm-cache restore, cold-cache rebuild, byte-identical outputs, and unchanged raw data: PASS")


if __name__ == "__main__":
    main()
