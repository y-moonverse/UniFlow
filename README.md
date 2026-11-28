# UniFlow – Smart Assignment & Exam Planner

UniFlow is a small web app that helps a university student answer one question:
**"Will I have enough time to finish this task before the deadline?"**

Instead of a single guess, each task gets a *three-point estimate* (optimistic, likely,
pessimistic hours). UniFlow runs a **Monte Carlo simulation** on those estimates and reports
the **probability that the task takes longer than the hours you have available**.

> Course project, Open Source Software. Built with Python and Streamlit.

---

## Screenshots

| Results table | Effort distribution | Weekly workload |
|---|---|---|
| ![Results](docs/screenshots/results.png) | ![Distribution](docs/screenshots/distribution.png) | ![Weekly workload](docs/screenshots/weekly.png) |

---

## Motivation

I wanted to create a tool that helps students manage their assignments and exams more
efficiently. Many traditional to-do list applications let users record tasks and deadlines,
but they do not consider the uncertainty in the time needed to complete each task. An
assignment may take less time than expected, while another may need several additional hours.
A single number such as "4 hours" hides this uncertainty, so I wanted to build a planner that
makes it visible and helps students see which tasks need an earlier start. Through this
project I also wanted to improve my Python programming skills and learn more about
probability and simulation.

The idea of turning a pile of deadlines into a realistic plan was inspired by
[Studyo](https://studyo.co/en/students). UniFlow is a separate, much smaller project with a
different approach (probabilistic risk analysis), and it does not reuse Studyo's code or design.

## Features

- **Three-point estimates** per task (optimistic / likely / pessimistic hours)
- **Monte Carlo simulation** with a Triangular distribution (100 to 10,000 iterations)
- **Overrun risk** per task: % of simulated runs that exceed your available hours, labelled
  Low (< 20%), Medium (20–50%) or High (≥ 50%)
- **Distribution chart** for any task, showing the mean, the P90 and your available hours
- **Weekly workload** chart comparing the P90 hours due each week with your study capacity
- **CSV upload** with validation and readable error messages, plus a downloadable template
- **Reproducible results** with an optional fixed random seed
- **Demo data that never goes stale:** the sample task dates shift automatically so the
  earliest task is always 2 days away
- **Unit tests** for the simulation logic (17 tests)

## How it works

1. **Three-point estimate.** For every task you provide `optimistic`, `likely` and
   `pessimistic` hours, plus the `available_hours` you can spend before the due date.
2. **Triangular distribution.** These three numbers define a triangular distribution: effort
   cannot be below the optimistic value or above the pessimistic one, and is most probable
   near the likely value. Its mean is `(optimistic + likely + pessimistic) / 3`.
3. **Monte Carlo simulation.** For each task the app draws N random effort values
   (default 1,000) from that distribution.
4. **Statistics from the draws**
   - `mean_effort`, `p50_effort`: typical effort
   - `p90_effort`: effort not exceeded in 90% of runs (a safe planning buffer)
   - `risk_score` = percentage of runs where effort > `available_hours`
5. **Weekly workload.** The P90 hours of all tasks due in the same week (weeks start on
   Monday) are added up and compared with your weekly study capacity.

### Example

Task `Assignment 1` with estimates 2 / 4 / 8 hours and 6 available hours: about 17% of the
simulated runs needed more than 6 hours, so the risk is **16.8% (Low)**.

## Installation & usage

Developed and tested with Python 3.14 (Python 3.10 or newer is recommended).

```bash
git clone https://github.com/y-moonverse/UniFlow.git
cd UniFlow

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser (usually http://localhost:8501). Choose **Sample data** in the
sidebar to try it immediately, or **Upload CSV** to use your own tasks.

### CSV format

| Column | Meaning | Example |
|---|---|---|
| `course` | Course name | Algorithms |
| `task_name` | Task name | Problem Set 4 |
| `due_date` | Deadline (`YYYY-MM-DD`) | 2026-11-25 |
| `optimistic` | Best-case hours | 3 |
| `likely` | Normal-case hours | 5 |
| `pessimistic` | Worst-case hours | 9 |
| `available_hours` | Hours you can spend before the deadline | 5 |

Rules: all hour columns must be numbers ≥ 0, and `optimistic ≤ likely ≤ pessimistic`.
A template can be downloaded from the app's sidebar; see also `sample_tasks.csv`.
(The dates in `sample_tasks.csv` are shifted automatically when the built-in sample data is
loaded; uploaded files are used exactly as they are.)

## Running the tests

```bash
python -m pytest
```

The tests cover input validation, the statistics of the simulation (for example that the
sample mean matches `(a+b+c)/3`), reproducibility with a fixed seed, risk scoring and the
weekly workload calculation.

## Project structure

```
UniFlow/
├── app.py                    # Streamlit user interface
├── simulation.py             # Validation, Monte Carlo simulation, risk, weekly workload
├── sample_tasks.csv          # Example data
├── tests/test_simulation.py  # Unit tests
├── conftest.py               # Lets pytest import simulation.py
├── requirements.txt
├── docs/screenshots/         # Images used in this README
├── LICENSE
└── README.md
```

`simulation.py` contains no Streamlit code on purpose, so the calculations can be tested
without starting the web app.

## Limitations

- The risk depends on the quality of the user's own estimates ("garbage in, garbage out").
- The Triangular distribution is a simple model; real effort may be skewed differently.
- Tasks are simulated independently. Real tasks compete for the same hours, which is not
  modelled.
- The weekly workload counts a task's P90 hours in the week it is **due**, instead of
  spreading them over the days before the deadline.
- Data is not stored: there are no accounts and no database.

## Possible future work

- Generate a day-by-day study schedule and compare different scheduling strategies
  (planned in the original project proposal, not implemented yet)
- Spread task effort over the days before each deadline
- Edit tasks inside the app and export results as CSV
- Correlated tasks and a combined "all tasks finish on time" probability

## References & credits

- Studyo, [studyo.co](https://studyo.co/en/students): source of the general idea (turning
  deadlines into a realistic plan). No code or assets were used.
- NumPy documentation, [`numpy.random.Generator.triangular`](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.triangular.html)
- [Streamlit](https://streamlit.io), [pandas](https://pandas.pydata.org), [Altair](https://altair-viz.github.io) and [pytest](https://pytest.org) (open-source libraries used as dependencies)
- Three-point estimation (PERT-style) and Monte Carlo simulation are standard
  project-management and statistics techniques.
- **AI assistance:** this project was developed with the help of Claude (Anthropic) for
  planning, code drafting, tests and documentation. I reviewed, ran and adapted the result.

## Author

[@y-moonverse](https://github.com/y-moonverse)

## License

Released under the [MIT License](LICENSE).
