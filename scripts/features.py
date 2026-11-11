"""Add duration and weekday features, preserving input data."""
from pathlib import Path
import pandas as pd


def feature_events(frame):
    result = frame.copy()
    result["duration_minutes"] = result.duration_seconds / 60
    dates = pd.to_datetime(result.timestamp, format="%Y-%m-%dT%H:%M:%S")
    result["weekday"] = dates.dt.day_of_week.map(dict(enumerate(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )))
    return result


def main():
    result = feature_events(pd.read_csv("data/transformed/events.csv", dtype={"user_id": "string"}))
    Path("data/features").mkdir(parents=True, exist_ok=True)
    result.to_csv("data/features/events.csv", index=False)


if __name__ == "__main__":
    main()
