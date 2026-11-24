import numpy as np
import pandas as pd
import pytest

from simulation import (
    run_monte_carlo_simulation,
    risk_level,
    sample_task_hours,
    validate_tasks,
    weekly_workload,
)


def make_df(**overrides):
    """One valid task; override any column to create edge cases."""
    row = {
        "course": "Algorithms",
        "task_name": "Problem Set",
        "due_date": "2026-11-20",
        "optimistic": 2,
        "likely": 4,
        "pessimistic": 8,
        "available_hours": 6,
    }
    row.update(overrides)
    return pd.DataFrame([row])


#  validation
def test_valid_data_passes():
    clean = validate_tasks(make_df())
    assert len(clean) == 1
    assert pd.api.types.is_datetime64_any_dtype(clean["due_date"])


def test_missing_column_raises():
    df = make_df().drop(columns=["available_hours"])
    with pytest.raises(ValueError, match="Missing required column"):
        validate_tasks(df)


def test_wrong_estimate_order_raises():
    with pytest.raises(ValueError, match="optimistic <= likely <= pessimistic"):
        validate_tasks(make_df(optimistic=10, likely=4, pessimistic=8))


def test_non_numeric_estimate_raises():
    with pytest.raises(ValueError, match="only numbers"):
        validate_tasks(make_df(likely="abc"))


def test_negative_hours_raises():
    with pytest.raises(ValueError, match="negative"):
        validate_tasks(make_df(optimistic=-1))


def test_bad_date_raises():
    with pytest.raises(ValueError, match="valid dates"):
        validate_tasks(make_df(due_date="not a date"))


#  simulation
def test_mean_and_p90_are_inside_the_estimate_range():
    res = run_monte_carlo_simulation(make_df(), num_simulations=5000, seed=1)
    row = res.iloc[0]
    assert 2 <= row["mean_effort"] <= 8
    assert row["mean_effort"] <= row["p90_effort"] <= 8


def test_mean_matches_triangular_formula():
    # Theory: mean of a triangular distribution = (a + b + c) / 3 = 14/3
    rng = np.random.default_rng(0)
    samples = sample_task_hours(2, 4, 8, 50000, rng)
    assert abs(samples.mean() - (2 + 4 + 8) / 3) < 0.05


def test_same_seed_is_reproducible_and_different_seed_differs():
    a = run_monte_carlo_simulation(make_df(), 2000, seed=7)
    b = run_monte_carlo_simulation(make_df(), 2000, seed=7)
    c = run_monte_carlo_simulation(make_df(), 2000, seed=8)
    assert a.equals(b)
    assert not a.equals(c)


def test_no_uncertainty_gives_constant_effort():
    df = make_df(optimistic=5, likely=5, pessimistic=5, available_hours=10)
    row = run_monte_carlo_simulation(df, 500, seed=1).iloc[0]
    assert row["mean_effort"] == 5
    assert row["p90_effort"] == 5
    assert row["risk_score"] == 0


#  risk
def test_risk_is_zero_when_budget_exceeds_pessimistic():
    row = run_monte_carlo_simulation(
        make_df(available_hours=9), 2000, seed=1).iloc[0]
    assert row["risk_score"] == 0
    assert row["risk_level"] == "Low"


def test_risk_is_100_when_budget_below_optimistic():
    row = run_monte_carlo_simulation(
        make_df(available_hours=1), 2000, seed=1).iloc[0]
    assert row["risk_score"] == 100
    assert row["risk_level"] == "High"


def test_risk_grows_as_budget_shrinks():
    big = run_monte_carlo_simulation(
        make_df(available_hours=7), 5000, seed=3).iloc[0]
    small = run_monte_carlo_simulation(
        make_df(available_hours=3), 5000, seed=3).iloc[0]
    assert small["risk_score"] > big["risk_score"]


def test_risk_level_thresholds():
    assert risk_level(0) == "Low"
    assert risk_level(19.9) == "Low"
    assert risk_level(20) == "Medium"
    assert risk_level(49.9) == "Medium"
    assert risk_level(50) == "High"


def test_days_left_uses_given_today():
    res = run_monte_carlo_simulation(
        make_df(due_date="2026-11-20"), 100, seed=1, today="2026-11-08")
    assert res.iloc[0]["days_left"] == 12


#  weekly workload
def test_weekly_workload_groups_by_week_and_flags_overload():
    results = pd.DataFrame({
        "due_date": pd.to_datetime(
            ["2026-11-09", "2026-11-13", "2026-11-17"]),  # Mon, Fri, next Tue
        "p90_effort": [10.0, 12.0, 5.0],
    })
    weekly = weekly_workload(results, weekly_capacity=20)
    assert len(weekly) == 2
    assert list(weekly["p90_hours"]) == [22.0, 5.0]
    assert list(weekly["overloaded"]) == [True, False]


def test_weekly_workload_empty_input():
    empty = pd.DataFrame({"due_date": [], "p90_effort": []})
    assert weekly_workload(empty, 20).empty
