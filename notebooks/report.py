import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd

    return Path, mo, pd, plt


@app.cell
def _(mo):
    mo.md("""
    # Event durations
    Durations in minutes from the reproducible DVC pipeline.
    """)
    return


@app.cell
def _(Path, pd):
    # Resolve relative to this notebook, independently of the working directory.
    events = pd.read_csv(Path(__file__).resolve().parents[1] / "data/features/events.csv")
    return (events,)


@app.cell
def _(events, plt):
    fig, ax = plt.subplots()
    ax.hist(events["duration_minutes"], bins=30, edgecolor="white")
    ax.set(xlabel="Duration (minutes)", ylabel="Number of events", title="Distribution of event durations")
    fig.tight_layout()
    fig
    return


if __name__ == "__main__":
    app.run()
