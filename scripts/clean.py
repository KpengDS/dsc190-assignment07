"""Validate events without altering the raw source."""
from datetime import datetime
from pathlib import Path
import argparse
import re

import pandas as pd

VALID_EVENT_TYPES = frozenset({"click", "login", "purchase", "scroll", "view"})
TIMESTAMP_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S",
)


def normalize_timestamp(value):
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass
    return None


def clean_events(frame):
    result = frame.copy().astype("string")
    present = result.notna().all(axis=1) & pd.DataFrame({
        col: result[col].str.strip().ne("") for col in result.columns
    }).all(axis=1)
    result = result.loc[present].copy()
    result = result.loc[result.event_type.isin(VALID_EVENT_TYPES)].copy()
    result["timestamp"] = result.timestamp.map(normalize_timestamp)
    result = result.dropna(subset=["timestamp"])
    # Reject fractional, nonnumeric, non-positive, and overflowing durations.
    def duration(value):
        if not re.fullmatch(r"[+]?[0-9]+", value):
            return None
        parsed = int(value)
        return parsed if 0 < parsed <= 2**63 - 1 else None
    durations = [duration(value) for value in result.duration_seconds]
    keep = [value is not None for value in durations]
    result = result.loc[keep].copy()
    result["duration_seconds"] = pd.array(
        [value for value in durations if value is not None], dtype="int64"
    )
    return result.reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", default="data/raw/events.csv")
    parser.add_argument("output", nargs="?", default="data/clean/events.csv")
    args = parser.parse_args()
    result = clean_events(pd.read_csv(args.source, dtype="string", keep_default_na=False))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
