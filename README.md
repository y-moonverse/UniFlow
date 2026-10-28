# UniFlow – A Smart Assignment and Exam Planner

## 1. Project Overview

UniFlow is a web application built with Python and Streamlit that helps students plan assignments and exams. Unlike a traditional to-do list, UniFlow estimates the time required for each task using three values: optimistic, likely, and pessimistic hours. It also analyzes deadline risks and generates schedules to help students manage their workload more effectively.

## 2. Motivation

I wanted to create a tool that helps students manage their assignments and exams more efficiently. Many traditional to-do list applications allow users to record tasks and deadlines, but they do not consider uncertainty in the time required to complete each task. For example, an assignment may take less time than expected, while another may require several additional hours. Therefore, I wanted to develop a planner that considers these uncertainties and helps students make more realistic study plans. Through this project, I also aim to improve my Python programming skills and learn more about probability, simulation, and optimization.

## 3. Goal

Build an open-source web application using Python and Streamlit that helps students organize academic tasks, estimate deadline risks, and generate effective study schedules. The application will use Monte Carlo simulation to estimate the probability of missing deadlines and compare different scheduling strategies to help students balance their daily workloads.

## 4. Main Features

### Task Management

- Load assignment and exam information from a CSV file.
- Store each task's course, task name, due date, and estimated effort.
- Represent task effort using optimistic, likely, and pessimistic hour estimates.
- Provide sample tasks through a demo mode for users who do not have their own CSV files.

### Deadline Risk Analysis

- Use Monte Carlo simulation to estimate the probability of missing each deadline.
- Randomly sample task completion times based on estimated effort.
- Calculate the estimated deadline risk for each task.
- Help students identify tasks that may require more preparation time.

### Scheduling System

- Implement an Earliest-Deadline-First (EDF) scheduling strategy.
- Implement a load-balanced scheduling strategy to distribute work more evenly across days.
- Compare scheduling strategies using peak daily workload and the number of overloaded days.
- Help students identify schedules that better balance their academic workload.

### Other Features

- Display task information and schedules through a Streamlit interface.
- Allow users to explore the application using sample data.
- Test important functions using pytest.
- If time remains, add an `.ics` calendar export feature so users can import their schedules into calendar applications.

## 5. Development Tools

- **Python:** Main programming language
- **Streamlit:** Build the web application interface
- **NumPy:** Generate random samples for Monte Carlo simulation
- **pandas:** Load and process task data from CSV files
- **pytest:** Test the application's functions
- **GitHub:** Share the project as open-source software

## 6. Expected Result

The expected result is a functional web application that helps students organize assignments and exams, estimate the risk of missing deadlines, and compare different study schedules. By considering uncertainty in task completion times, UniFlow aims to provide more realistic planning suggestions than a traditional to-do list.

## 7. Conclusion

UniFlow combines academic task management with probabilistic deadline analysis and workload scheduling. Through this project, I aim to develop a useful open-source application while applying Python programming, random sampling, probability distributions, Monte Carlo simulation, and basic optimization concepts. The project will also help me understand how these concepts can be applied to solve practical problems in students' daily lives.
