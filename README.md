# Student Result Prediction ML Application — CI/CD and Docker

This educational project demonstrates an end-to-end machine-learning CI and Continuous Delivery workflow using GitHub Actions, Flask, scikit-learn, and Docker.

## Workflow

1. Install Python dependencies.
2. Generate reproducible synthetic student data and train a Logistic Regression model.
3. Save the trained model and evaluation metrics.
4. Enforce the minimum model-accuracy quality gate (85%).
5. Run automated ML pipeline tests.
6. Run Flask prediction API tests.
7. Upload the generated ML artifacts.
8. Package the validated application, trained model, metrics, dependencies, and Docker configuration as a release candidate.
9. Build and run the Docker image manually using the downloaded release candidate.

**Continuous Delivery prepares a release candidate; it does not deploy the application to a production server.** Docker image building and container testing are currently manual steps, not GitHub Actions steps.

## Project files

- `train_model.py` — generates demonstration data, trains/evaluates the model, and saves outputs.
- `quality_gate.py` — fails the workflow when accuracy is below 85%.
- `test_ml_pipeline.py` — automated ML pipeline tests.
- `app.py` — Flask health and prediction API.
- `test_app.py` — API tests.
- `Dockerfile` — packages the Flask app, trained model, runtime, and dependencies into an image.
- `.dockerignore` — excludes tests, Git metadata, and other unnecessary files from the Docker build context.
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

## Build and run with Docker

Docker Desktop or Docker Engine must be installed and running.

1. Open the repository's **Actions** tab.
2. Select a successful **Student Result ML CI-CD** workflow run.
3. Download the `student-result-ml-release` artifact and extract it.
4. Open a terminal in the extracted folder containing `Dockerfile`, `app.py`, and `student_result_model.pkl`.
5. Build the image:

```bash
docker build -t student-result-ml:1.0 .
```

6. Run the container:

```bash
docker run --rm --name student-result-ml-container -p 5000:5000 student-result-ml:1.0
```

7. Open `http://localhost:5000/` to check the health endpoint. Send a JSON POST request to `http://localhost:5000/predict` to test predictions.

To stop the container, press `Ctrl+C` in the terminal running it. If it was started in detached mode, use `docker stop student-result-ml-container`.

## Download the workflow artifacts

The workflow uploads two artifacts, retained for seven days:

- **student-result-ml-artifacts** — trained model, metrics, and generated demonstration dataset.
- **student-result-ml-release** — `app.py`, `student_result_model.pkl`, `metrics.json`, `requirements.txt`, `Dockerfile`, `.dockerignore`, and `DEPLOYMENT.txt`.

Artifacts are downloadable workflow outputs; they are not automatically committed to the source repository.

## Important limitation

The dataset is synthetic and intended for learning CI/CD. This model is not validated for real student assessment decisions.
