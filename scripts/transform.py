"""Add calendar dates to cleaned events."""
from pathlib import Path
import pandas as pd


def transform_events(frame):
    result = frame.copy()
    result["date"] = pd.to_datetime(result.timestamp, format="%Y-%m-%dT%H:%M:%S").dt.strftime("%Y-%m-%d")
    return result


def main():
    result = transform_events(pd.read_csv("data/clean/events.csv", dtype={"user_id": "string"}))
    Path("data/transformed").mkdir(parents=True, exist_ok=True)
    result.to_csv("data/transformed/events.csv", index=False)


if __name__ == "__main__":
    main()
