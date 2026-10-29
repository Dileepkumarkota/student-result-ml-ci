# Student Result Prediction ML Application — CI/CD

This educational project demonstrates an end-to-end machine-learning CI and Continuous Delivery workflow using GitHub Actions.

## Workflow
1. Install Python dependencies.
2. Generate reproducible synthetic student data and train a Logistic Regression model.
3. Save the trained model and evaluation metrics.
4. Enforce the minimum model-accuracy quality gate (85%).
5. Run automated ML pipeline tests.
6. Run Flask prediction API tests.
7. Upload the generated ML artifacts.
8. Package the validated application as a release candidate and upload it as a separate workflow artifact.

**Continuous Delivery prepares a release candidate; it does not deploy the application to a production server.**

## Project files
- `train_model.py` — generates demonstration data, trains/evaluates the model, and saves outputs.
- `quality_gate.py` — fails the workflow when accuracy is below 85%.
- `test_ml_pipeline.py` — automated ML pipeline tests.
- `app.py` — Flask health and prediction API.
- `test_app.py` — API tests.
- `.github/workflows/ml-ci.yml` — CI/CD workflow.

## Prediction API
The API expects four numeric features: `attendance`, `internal_marks`, `assignment_marks`, and `previous_score`.

Start locally after training:
```bash
python -m pip install -r requirements.txt
python train_model.py
python quality_gate.py
python app.py
```

Health check: `GET http://127.0.0.1:5000/`

Prediction: send a JSON `POST` request to `http://127.0.0.1:5000/predict`:
```json
{
  "attendance": 90,
  "internal_marks": 85,
  "assignment_marks": 88,
  "previous_score": 80
}
```

The API responds with a `PASS` or `FAIL` prediction and a numeric prediction code. Missing or non-numeric fields are rejected.

## Download the workflow artifacts
Open the repository's **Actions** tab, choose a successful **Student Result ML CI-CD** run, and download either artifact:

- **student-result-ml-artifacts** — trained model, metrics, and generated demonstration dataset.
- **student-result-ml-release** — `app.py`, `student_result_model.pkl`, `metrics.json`, `requirements.txt`, and `DEPLOYMENT.txt`.

Artifacts are retained for seven days. They are downloadable workflow outputs and are not automatically committed to the source repository.

## Important limitation
The dataset is synthetic and intended for learning CI/CD. This model is not validated for real student assessment decisions.
