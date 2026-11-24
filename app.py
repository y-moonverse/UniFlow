import os

import altair as alt
import pandas as pd
import streamlit as st

from simulation import (
    REQUIRED_COLUMNS,
    simulate_samples,
    summarize,
    validate_tasks,
    weekly_workload,
)

st.set_page_config(
    page_title="UniFlow - Smart Assignment Planner", layout="wide")

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_tasks.csv")

RISK_COLORS = {"Low": "#2e9e5b", "Medium": "#e6a23c", "High": "#d9534f"}

st.title("UniFlow 🚀")
st.subheader("Smart Assignment & Exam Planner with Risk Analysis")
st.markdown(
    "UniFlow uses **three-point estimates** (optimistic, likely, pessimistic hours) "
    "and a **Monte Carlo simulation** to estimate the chance that each task takes "
    "more time than you have available before its deadline."
)


# Data loading
def load_sample():
    if not os.path.exists(SAMPLE_PATH):
        return None
    df = pd.read_csv(SAMPLE_PATH)
    # Shift the sample dates so the earliest task is always 2 days away
    # (demo data never goes stale, whenever the app is run)
    dates = pd.to_datetime(df["due_date"])
    shift = (pd.Timestamp.today().normalize() +
             pd.Timedelta(days=2)) - dates.min()
    df["due_date"] = (dates + shift).dt.strftime("%Y-%m-%d")
    return df


@st.cache_data(show_spinner="Simulating task completion times...")
def simulate(tasks, num_simulations, seed, run_id):
    """Cached so that changing a chart selection does not re-randomize results.
    `run_id` only exists to force a fresh run when the user clicks Re-run."""
    samples = simulate_samples(tasks, num_simulations, seed)
    return summarize(tasks, samples), samples


# Sidebar
st.sidebar.header("Navigation & Settings")

source = st.sidebar.radio("Data source", ["Sample data", "Upload CSV"])

num_simulations = st.sidebar.slider(
    "Simulation iterations", min_value=100, max_value=10000, value=1000, step=100)

fixed_seed = st.sidebar.checkbox(
    "Fixed random seed (reproducible)", value=True)
seed = 42 if fixed_seed else None

weekly_capacity = st.sidebar.slider(
    "Study hours available per week", min_value=5, max_value=60, value=25)

if "run_id" not in st.session_state:
    st.session_state.run_id = 0
if st.sidebar.button("🔁 Re-run simulation"):
    st.session_state.run_id += 1

template = pd.DataFrame([{
    "course": "Algorithms", "task_name": "Problem Set 1", "due_date": "2026-12-01",
    "optimistic": 2, "likely": 4, "pessimistic": 8, "available_hours": 6,
}])
st.sidebar.download_button(
    "⬇️ Download CSV template",
    data=template.to_csv(index=False),
    file_name="uniflow_template.csv",
    mime="text/csv",
)

# Load + validate the chosen data
if source == "Sample data":
    raw = load_sample()
    if raw is None:
        st.error("sample_tasks.csv not found next to app.py.")
        st.stop()
else:
    uploaded = st.file_uploader("Choose your CSV file", type="csv")
    if uploaded is None:
        st.info(
            "Upload a CSV with these columns: "
            + ", ".join(f"`{c}`" for c in REQUIRED_COLUMNS)
            + ". You can download a template from the sidebar."
        )
        st.stop()
    try:
        raw = pd.read_csv(uploaded)
    except Exception as exc:  # unreadable / empty file
        st.error(f"Could not read that file: {exc}")
        st.stop()

try:
    tasks = validate_tasks(raw)
except ValueError as exc:
    st.error(f"Problem with the data: {exc}")
    st.stop()

# Run simulation
results, samples = simulate(
    tasks, num_simulations, seed, st.session_state.run_id)

high = int((results["risk_level"] == "High").sum())
medium = int((results["risk_level"] == "Medium").sum())

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total active tasks", len(results))
with col2:
    st.metric("Simulation iterations", f"{num_simulations:,} runs")
with col3:
    if high:
        st.metric("Status", "Attention needed 🔴")
        st.caption(f"{high} high-risk task(s)")
    elif medium:
        st.metric("Status", "Watch closely 🟡")
        st.caption(f"{medium} medium-risk task(s)")
    else:
        st.metric("Status", "On track 🟢")
        st.caption("All tasks low risk")

st.markdown("---")

tab_results, tab_dist, tab_week, tab_about = st.tabs(
    ["📋 Results", "🎲 Distribution", "📅 Weekly workload", "ℹ️ How it works"])

#  Results
with tab_results:
    sort_by = st.radio(
        "Sort by", ["Due date", "Risk (highest first)"], horizontal=True)
    shown = results.sort_values(
        "due_date" if sort_by == "Due date" else "risk_score",
        ascending=(sort_by == "Due date"),
    ).copy()
    shown["due_date"] = shown["due_date"].dt.strftime("%Y-%m-%d")

    st.dataframe(
        shown,
        hide_index=True,
        column_config={
            "course": "Course",
            "task_name": "Task",
            "due_date": "Due",
            "days_left": st.column_config.NumberColumn("Days left"),
            "available_hours": st.column_config.NumberColumn("Available (h)"),
            "mean_effort": st.column_config.NumberColumn("Mean (h)"),
            "p50_effort": st.column_config.NumberColumn("Median (h)"),
            "p90_effort": st.column_config.NumberColumn("P90 (h)"),
            "risk_score": st.column_config.ProgressColumn(
                "Overrun risk", min_value=0, max_value=100, format="%.0f%%"),
            "risk_level": "Level",
        },
    )

    overdue = results[results["days_left"] < 0]
    if not overdue.empty:
        st.warning(f"{len(overdue)} task(s) are past their due date.")

#  Distribution
with tab_dist:
    labels = {i: f"{r.course} - {r.task_name}" for i, r in results.iterrows()}
    choice = st.selectbox("Task", list(labels.keys()),
                          format_func=lambda i: labels[i])
    row = results.loc[choice]

    hist_data = pd.DataFrame({"hours": samples[choice]})
    hist = (
        alt.Chart(hist_data)
        .mark_bar(opacity=0.75)
        .encode(
            x=alt.X("hours:Q", bin=alt.Bin(maxbins=40),
                    title="Simulated effort (hours)"),
            y=alt.Y("count()", title="Simulation runs"),
        )
    )
    markers = pd.DataFrame({
        "label": ["Mean", "P90", "Available hours"],
        "hours": [row["mean_effort"], row["p90_effort"], row["available_hours"]],
    })
    lines = (
        alt.Chart(markers)
        .mark_rule(strokeWidth=3)
        .encode(
            x="hours:Q",
            color=alt.Color(
                "label:N",
                scale=alt.Scale(
                    domain=["Mean", "P90", "Available hours"],
                    range=["#1f77b4", "#e6a23c", "#d9534f"]),
                legend=alt.Legend(title=None)),
        )
    )
    st.altair_chart(hist + lines)

    st.markdown(
        f"**{row['risk_score']:.0f}%** of the simulated runs needed more than "
        f"your **{row['available_hours']:.0f} available hours** "
        f"(risk level: **{row['risk_level']}**)."
    )

#  Weekly workload
with tab_week:
    weekly = weekly_workload(results, weekly_capacity)
    bars = (
        alt.Chart(weekly)
        .mark_bar()
        .encode(
            x=alt.X("week_label:N", sort=None, title=None),
            y=alt.Y("p90_hours:Q", title="P90 hours due that week"),
            color=alt.condition(
                alt.datum.overloaded == True,  # noqa: E712
                alt.value(RISK_COLORS["High"]),
                alt.value(RISK_COLORS["Low"])),
            tooltip=["week_label", "p90_hours", "capacity"],
        )
    )
    cap_line = (
        alt.Chart(pd.DataFrame({"capacity": [float(weekly_capacity)]}))
        .mark_rule(strokeDash=[6, 4], strokeWidth=2, color="gray")
        .encode(y="capacity:Q")
    )
    st.altair_chart(bars + cap_line)

    over = weekly[weekly["overloaded"]]
    if over.empty:
        st.success("No week exceeds your available study hours.")
    else:
        st.warning(
            "Overloaded week(s): " + ", ".join(over["week_label"])
            + ". Consider starting those tasks earlier."
        )
    st.caption(
        "Simplification: each task's P90 hours are counted in the week it is due.")

#  About
with tab_about:
    st.markdown("""
**Three-point estimate.** For each task you give three numbers: *optimistic* (everything
goes well), *likely* (normal case) and *pessimistic* (things go wrong).

**Triangular distribution.** These three numbers define a triangle: effort can't be below
the optimistic value or above the pessimistic one, and is most probable near the likely value.
The expected effort is `(optimistic + likely + pessimistic) / 3`.

**Monte Carlo simulation.** We draw thousands of random effort values per task. Statistics
over those draws give:
- **Mean / Median:** typical effort.
- **P90:** effort that was not exceeded in 90% of runs (a safe buffer for planning).
- **Overrun risk:** the percentage of runs that needed *more* hours than `available_hours`.
  Low is under 20%, Medium is 20-50%, High is 50% or more.

**Weekly workload.** Adds the P90 hours of tasks due in each week and compares the total
with your weekly study capacity.
""")
