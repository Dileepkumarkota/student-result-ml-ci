# Student Result Prediction ML Model with GitHub Actions CI

This educational project demonstrates an ML continuous-integration pipeline. GitHub Actions installs dependencies, generates synthetic student data, trains and evaluates a Logistic Regression classifier, saves the model and metrics, and runs automated tests.

## Pipeline
1. Set up Python 3.11 and install `requirements.txt`.
2. Generate 300 reproducible demonstration records.
3. Split data into 80% training and 20% testing.
4. Scale features and train Logistic Regression.
5. Save the model and evaluation metrics.
6. Run seven automated tests.

## Features
- `attendance`: attendance percentage
- `internal_marks`: internal assessment marks
- `assignment_marks`: assignment marks
- `previous_score`: previous academic score

Target: `result` (1 = PASS, 0 = FAIL).

## Run locally
```bash
python -m pip install -r requirements.txt
python train_model.py
python -m unittest discover -v
```

Generated runtime files: `student_results.csv`, `student_result_model.pkl`, and `metrics.json`. GitHub Actions does not automatically commit these files.

The workflow at `.github/workflows/ml-ci.yml` runs on pushes and pull requests to `main`, or manually from the Actions tab.

**Note:** This uses synthetic data for teaching CI; it is not a validated model for real student decisions. Check actual accuracy in the workflow logs or `metrics.json`.
