# Student Result Prediction ML Model with GitHub Actions CI

This educational project demonstrates an ML continuous-integration pipeline. GitHub Actions installs dependencies, generates synthetic student data, trains and evaluates a Logistic Regression classifier, saves the model and metrics, checks a model-accuracy quality gate, runs automated tests, and uploads validated outputs as a downloadable workflow artifact.

## Pipeline
1. Set up Python 3.11 and install `requirements.txt`.
2. Generate 300 reproducible demonstration records.
3. Split data into 80% training and 20% testing.
4. Scale features and train Logistic Regression.
5. Save the model and evaluation metrics.
6. Check model accuracy using `quality_gate.py` (minimum 85%).
7. Run automated tests.
8. Upload the model, metrics, and generated dataset as the `student-result-ml-artifacts` artifact for seven days.

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
python quality_gate.py
python -m unittest discover -v
```

## Download generated ML artifacts
After a successful GitHub Actions run, open the repository's **Actions** tab, select the latest **Student Result ML CI** run, and download **student-result-ml-artifacts** from the Artifacts section. The archive contains:
- `student_result_model.pkl` — trained model
- `metrics.json` — evaluation metrics
- `student_results.csv` — generated demonstration dataset

The artifact is retained for seven days. These generated files are stored as a workflow artifact, not automatically committed to the source repository.

The workflow at `.github/workflows/ml-ci.yml` runs on pushes and pull requests to `main`, or manually from the Actions tab.

**Note:** This uses synthetic data for teaching CI; it is not a validated model for real student decisions. Check actual accuracy in the workflow logs or `metrics.json`.
