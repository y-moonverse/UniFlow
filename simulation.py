"""
UniFlow - Monte Carlo simulation core.

Each task has a three-point estimate (optimistic / likely / pessimistic hours).
We model the real effort of a task with a Triangular distribution and run many
random simulations to answer: "How likely is this task to take MORE hours than
I have available before its deadline?"

This module has no Streamlit code, so it can be unit tested on its own.
"""

import numpy as np
import pandas as pd

ESTIMATE_COLUMNS = ["optimistic", "likely", "pessimistic", "available_hours"]
REQUIRED_COLUMNS = ["course", "task_name", "due_date"] + ESTIMATE_COLUMNS

# Risk thresholds (percentage of simulation runs that overrun the time budget)
MEDIUM_RISK_THRESHOLD = 20.0
HIGH_RISK_THRESHOLD = 50.0


# 1. Input validation

def validate_tasks(df):
    """
    Check a task table and return a cleaned copy.

    Raises ValueError with a readable message if the data cannot be simulated
    (np.random.triangular would otherwise crash or give nonsense).
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")
    if df.empty:
        raise ValueError("The task table is empty.")

    clean = df.copy()

    # Numeric columns: convert, then reject blanks / text
    for col in ESTIMATE_COLUMNS:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
    if clean[ESTIMATE_COLUMNS].isna().any().any():
        raise ValueError(
            "Estimate columns must contain only numbers (no blanks or text).")
    if (clean[ESTIMATE_COLUMNS] < 0).any().any():
        raise ValueError("Hours cannot be negative.")

    # Triangular distribution needs optimistic <= likely <= pessimistic
    in_order = (clean["optimistic"] <= clean["likely"]) & (
        clean["likely"] <= clean["pessimistic"])
    if not in_order.all():
        bad = ", ".join(clean.loc[~in_order, "task_name"].astype(str))
        raise ValueError(
            "Estimates must satisfy optimistic <= likely <= pessimistic. "
            f"Please check: {bad}")

    # Dates
    clean["due_date"] = pd.to_datetime(clean["due_date"], errors="coerce")
    if clean["due_date"].isna().any():
        raise ValueError("due_date must contain valid dates like 2026-11-30.")

    return clean.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Simulation
# ---------------------------------------------------------------------------
def sample_task_hours(optimistic, likely, pessimistic, num_simulations, rng):
    """Draw random effort values (hours) for ONE task."""
    if optimistic == pessimistic:
        # Degenerate case: no uncertainty. numpy raises an error if left == right.
        return np.full(num_simulations, float(optimistic))
    return rng.triangular(optimistic, likely, pessimistic, num_simulations)


def simulate_samples(df, num_simulations=1000, seed=None):
    """
    Run the simulation for every task.

    Returns a dict {row_index: numpy array of simulated hours}.
    `df` must already be validated (see validate_tasks).
    """
    rng = np.random.default_rng(seed)
    samples = {}
    for index, row in df.iterrows():
        samples[index] = sample_task_hours(
            row["optimistic"], row["likely"], row["pessimistic"],
            num_simulations, rng)
    return samples


# ---------------------------------------------------------------------------
# 3. Summary statistics and risk
# ---------------------------------------------------------------------------
def risk_level(score):
    """Turn a risk percentage into a label."""
    if score >= HIGH_RISK_THRESHOLD:
        return "High"
    if score >= MEDIUM_RISK_THRESHOLD:
        return "Medium"
    return "Low"


def summarize(df, samples, today=None):
    """
    Build the results table from simulated samples.

    risk_score = % of simulation runs where the task needed MORE hours than
    `available_hours` (i.e. the probability of missing the deadline).
    """
    today = pd.Timestamp.today() if today is None else pd.Timestamp(today)
    rows = []
    for index, row in df.iterrows():
        hours = samples[index]
        score = float(np.mean(hours > row["available_hours"]) * 100)
        rows.append({
            "course": row["course"],
            "task_name": row["task_name"],
            "due_date": row["due_date"],
            "days_left": int((row["due_date"].normalize() - today.normalize()).days),
            "available_hours": round(float(row["available_hours"]), 1),
            "mean_effort": round(float(np.mean(hours)), 1),
            "p50_effort": round(float(np.percentile(hours, 50)), 1),
            "p90_effort": round(float(np.percentile(hours, 90)), 1),
            "risk_score": round(score, 1),
            "risk_level": risk_level(score),
        })
    return pd.DataFrame(rows)


def run_monte_carlo_simulation(df, num_simulations=1000, seed=None,
                               today=None, return_samples=False):
    """
    Validate -> simulate -> summarize.

    Returns the results DataFrame (and the raw samples if return_samples=True).
    """
    clean = validate_tasks(df)
    samples = simulate_samples(clean, num_simulations, seed)
    results = summarize(clean, samples, today)
    if return_samples:
        return results, samples
    return results


# ---------------------------------------------------------------------------
# 4. Weekly workload
# ---------------------------------------------------------------------------
def weekly_workload(results, weekly_capacity):
    """
    Add up the P90 effort of all tasks due in each week (weeks start Monday)
    and compare it with the hours the student can work per week.

    Simplification: a task's hours are counted in the week it is DUE, not
    spread across the days before it.
    """
    if results.empty:
        return pd.DataFrame(
            columns=["week_start", "week_label", "p90_hours", "capacity", "overloaded"])

    due = pd.to_datetime(results["due_date"])
    week_start = (due - pd.to_timedelta(due.dt.day_of_week,
                  unit="D")).dt.normalize()

    weekly = (
        pd.DataFrame({"week_start": week_start,
                     "p90_hours": results["p90_effort"]})
        .groupby("week_start", as_index=False)["p90_hours"].sum()
        .sort_values("week_start")
        .reset_index(drop=True)
    )
    weekly["p90_hours"] = weekly["p90_hours"].round(1)
    weekly["week_label"] = "Week of " + \
        weekly["week_start"].dt.strftime("%b %d")
    weekly["capacity"] = float(weekly_capacity)
    weekly["overloaded"] = weekly["p90_hours"] > weekly["capacity"]
    return weekly
