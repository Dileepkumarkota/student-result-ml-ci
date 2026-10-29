# Student Result Prediction ML Application — CI/CD and Docker

This educational project demonstrates an end-to-end machine-learning CI and Continuous Delivery workflow using GitHub Actions, Flask, scikit-learn, and Docker.

## Automated workflow

For pushes to `main`, pull requests targeting `main`, and manual runs, GitHub Actions:

1. Installs Python dependencies.
2. Generates demonstration student data and trains a Logistic Regression model.
3. Saves the trained model and evaluation metrics.
4. Enforces the minimum model-accuracy quality gate (85%).
5. Runs automated ML pipeline and Flask API tests.
6. Builds a Docker image tagged with the current Git commit SHA.
7. Starts the container and retries `GET /health` until the service is ready (up to about 30 seconds).
8. Sends a real JSON request to `POST /predict` and verifies the response contains a `PASS` or `FAIL` prediction.
9. Captures container logs and removes the container even if a preceding step fails.
10. Uploads the validated ML artifacts and release-candidate files.

**This practical automates Docker build and runtime testing in CI. It does not publish the image to a container registry or deploy it to production.**

## Project files

- `train_model.py` — creates synthetic data, trains/evaluates the model, and saves outputs.
- `quality_gate.py` — fails the workflow when accuracy is below 85%.
- `test_ml_pipeline.py` — automated ML pipeline tests.
- `app.py` — Flask health and prediction API.
- `test_app.py` — API tests, including the dedicated health endpoint.
- `Dockerfile` and `.dockerignore` — container build configuration.
- `.github/workflows/ml-ci.yml` — CI/CD workflow with Docker runtime validation.

## Run locally

Use Python 3.11 or a compatible environment:

```bash
python -m pip install -r requirements.txt
python train_model.py
python quality_gate.py
python -m unittest test_ml_pipeline.py -v
python -m unittest test_app.py -v
python app.py
```

Health check: `GET http://127.0.0.1:5000/health` (also available at `/`).

Prediction: send a JSON `POST` request to `http://127.0.0.1:5000/predict`:

```json
{
  "attendance": 90,
  "internal_marks": 85,
  "assignment_marks": 88,
  "previous_score": 80
}
```

## Run with Docker locally

After running `python train_model.py` so the model and metrics files exist:

```bash
docker build -t student-result-ml:1.0 .
docker run --rm --name student-result-ml-container -p 5000:5000 student-result-ml:1.0
```

Then open `http://localhost:5000/health` or send a JSON POST request to `http://localhost:5000/predict`. Docker Desktop or Docker Engine must be installed and running.

## Workflow artifacts

The workflow uploads two artifacts, retained for seven days:

- `student-result-ml-artifacts` — trained model, metrics, and generated demonstration dataset.
- `student-result-ml-release` — app, model, metrics, dependencies, Docker configuration, and deployment notes.

Open the repository's **Actions** tab, select a workflow run, and download the artifact from that run. Artifacts are workflow outputs; they are not automatically committed to the source repository.

## Important limitation

The dataset is synthetic and intended for learning CI/CD. This model has not been validated for real student assessment decisions.
