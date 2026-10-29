# Practical 12 — Monitor the Student Result Prediction API with Prometheus and Grafana

**Running project:** Student Result Prediction  
**Continuation:** Practical 11 — Logging and Error Tracking

## 1. Aim

Instrument the deployed Student Result Prediction FastAPI service with Prometheus metrics, collect metrics using Prometheus, visualize operational behavior in Grafana, and configure simple alert rules for repeated client errors or service unavailability.

## 2. Learning objectives

- Understand logs, metrics, dashboards, and alerts.
- Expose application metrics at `/metrics`.
- Measure HTTP requests, latency, prediction attempts, HTTP status codes, and model readiness.
- Reuse Practical 11 logging and error tracking.
- Build, test, publish, and redeploy through GitHub Actions → GHCR → Render.
- Scrape the public Render `/metrics` endpoint with Prometheus.
- Create Grafana panels and basic PromQL queries.
- Configure and observe Prometheus alert rules without exposing student data or secrets.

## 3. Architecture

The FastAPI application exposes metrics. Prometheus periodically scrapes `/metrics` and stores time series. Grafana queries Prometheus and displays dashboards. Prometheus alert rules evaluate conditions over collected metrics.

## 4. Prerequisites

- Practical 11 completed and the API running on Render.
- Existing repository and GitHub Actions workflow from Practical 9.
- Existing GHCR image and Render service.
- Docker Engine/Desktop, Python/FastAPI files, internet access, and a browser.
- Actual public Render hostname, e.g. `student-result-prediction.onrender.com`.

Confirm the real app port and `/health` route in this repository before following port examples below.

## 5. Add the Prometheus dependency

Add `prometheus-client` to `requirements.txt`, preserving all existing dependencies such as FastAPI, Uvicorn, pandas, scikit-learn, and joblib.

## 6. Add application metrics

Keep the existing Practical 11 logging code. Add these imports to `app.py`:

```python
import time
from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
```

Define each metric once at module level, near the logger configuration and before endpoint functions:

```python
HTTP_REQUESTS = Counter(
    "student_api_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "student_api_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
PREDICTIONS = Counter(
    "student_api_predictions_total",
    "Prediction inference attempts",
    ["result"],
)
MODEL_LOADED = Gauge(
    "student_api_model_loaded",
    "Whether the prediction model loaded successfully",
)
```

### Connect model loading to the readiness gauge

Keep the existing model-loading logic and logger. Set the gauge after successful loading, and set it to zero on failure:

```python
try:
    model = joblib.load(MODEL_FILE)  # retain the existing path and variable names
    MODEL_LOADED.set(1)
    logger.info("event=model_loaded")
except Exception:
    MODEL_LOADED.set(0)
    logger.exception("event=model_load_failed")
    raise
```

Adapt `MODEL_FILE` and `model` to the names already used by your app. Do not change model preprocessing or feature ordering.

### Extend the Practical 11 request middleware

Extend the existing middleware instead of adding duplicate middleware. Record elapsed time and status after `call_next` returns:

```python
@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        path = request.url.path
        HTTP_REQUESTS.labels(
            method=request.method, path=path, status=str(status)
        ).inc()
        HTTP_REQUEST_DURATION.labels(
            method=request.method, path=path
        ).observe(elapsed)
```

**Integration note:** merge this metric logic into the existing Practical 11 middleware, preserving its request ID, logging, response header, and exception handling. Do not register two overlapping copies of the same middleware. For larger production systems, prefer route templates over raw paths to avoid high-cardinality labels.

### Count prediction attempts

Preserve the existing `StudentResultInput` schema and current preprocessing/prediction code. Increment the counter around actual inference attempts, and keep the Practical 11 safe logs:

```python
@app.post("/predict")
def predict(data: StudentResultInput):
    try:
        # Preserve the project's existing preprocessing and feature ordering.
        input_data = data.model_dump()  # data.dict() for older Pydantic versions
        input_df = pd.DataFrame([input_data])
        prediction = model.predict(input_df)

        PREDICTIONS.labels(result="success").inc()
        logger.info("event=prediction_succeeded")
        return {"prediction": prediction[0]}
    except Exception:
        PREDICTIONS.labels(result="error").inc()
        logger.exception("event=prediction_failed")
        raise
```

This is an integration example: use the existing endpoint's real variable names and preprocessing. Do not replace a trained pipeline's required transformations with a generic DataFrame if that changes model behavior. Avoid logging student identifiers, full payloads, or secrets.

### Expose the metrics endpoint

Add once to the FastAPI application:

```python
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

The metrics endpoint must not expose passwords, tokens, student names, registration numbers, or raw student records. For production, restrict metrics access to the monitoring network where possible.

## 7. Run and test locally

Use the project's configured port. The classroom example is:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/metrics`

Send several valid prediction requests using the exact existing API schema, then generate a validation error (missing required field or wrong type) and a 404 request to a nonexistent route. Check that the metrics update. The model readiness gauge should be `1` after successful model loading.

Example metric names and shapes:

```text
student_api_http_requests_total{method="GET",path="/health",status="200"} 1
student_api_http_requests_total{method="POST",path="/predict",status="200"} 3
student_api_predictions_total{result="success"} 3
student_api_model_loaded 1
student_api_http_request_duration_seconds_bucket{...}
```

Actual values depend on requests made and the histogram buckets.

## 8. Build and test the Docker image

```bash
docker build -t student-result-prediction:practical12 .
docker run --rm -p 8000:8000 --name student-result-p12 student-result-prediction:practical12
```

Adjust the port mapping to match the app's real internal port. Retest `/health`, `/predict`, and `/metrics`, and verify Practical 11 logs still appear.

## 9. Commit, publish, and redeploy

Commit the app and dependency changes using the repository's established workflow. Example:

```bash
git add app.py requirements.txt
git commit -m "Add Prometheus metrics for Practical 12"
git push
```

If using a feature branch and pull requests, open a PR and merge it to `main` according to class policy.

1. Open [GitHub Actions](https://github.com/Dileepkumarkota/student-result-ml-ci/actions).
2. Confirm the Practical 9 workflow builds and tests the Docker image and publishes it to GHCR only after checks pass.
3. Confirm the updated image tag in [GitHub Packages](https://github.com/users/Dileepkumarkota/packages).
4. Open the existing Render service and manually deploy the latest image/reference.
5. Verify public `/health`, `/docs`, and `/metrics` endpoints.

GHCR publishing requires package write access. If the push fails with `permission_denied: write_package`, grant `Dileepkumarkota/student-result-ml-ci` write access in the package's **Manage Actions access** settings.

## 10. Configure Prometheus

Create a local folder named `Practical_12_Monitoring` and add `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/student_api_alerts.yml

scrape_configs:
  - job_name: "student-result-api"
    scheme: https
    metrics_path: /metrics
    static_configs:
      - targets:
          - "<render-service>.onrender.com"
```

Replace the placeholder with the actual Render hostname only—no `https://` prefix in `targets`, because `scheme: https` is configured separately.

Create `student_api_alerts.yml`:

```yaml
groups:
  - name: student-result-api-alerts
    rules:
      - alert: StudentAPIClientErrors
        expr: sum(rate(student_api_http_requests_total{status=~"4.."}[2m])) > 0
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "Student Result API is receiving client errors"
          description: "4xx responses have been observed during the recent window."

      - alert: StudentAPIDown
        expr: up{job="student-result-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Student Result API monitoring target is down"
          description: "Prometheus cannot scrape the deployed API."
```

These are simple classroom thresholds, not production recommendations. Production thresholds should reflect realistic traffic and service objectives.

## 11. Start Prometheus in Docker

Create a Docker network (if it already exists, reuse it):

```bash
docker network create mlops-monitoring
```

From the monitoring folder, start Prometheus:

```bash
docker run -d \
  --name prometheus \
  --network mlops-monitoring \
  -p 9090:9090 \
  -v "${PWD}/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  -v "${PWD}/student_api_alerts.yml:/etc/prometheus/student_api_alerts.yml:ro" \
  prom/prometheus
```

If your shell does not expand `${PWD}`, use absolute host paths. Open [Prometheus targets](http://localhost:9090/targets). The `student-result-api` target should show **UP**. If it is DOWN, first test the public Render `/metrics` URL, then check the hostname, HTTPS scheme, and Prometheus configuration.

## 12. PromQL queries

Use these queries in the Prometheus expression browser:

| Question | PromQL |
|---|---|
| Is the model loaded? | `student_api_model_loaded` |
| Total requests | `sum(student_api_http_requests_total)` |
| Current request rate | `sum(rate(student_api_http_requests_total[1m]))` |
| Successful predictions | `sum(student_api_predictions_total{result="success"})` |
| Failed inference attempts | `sum(student_api_predictions_total{result="error"})` |
| 4xx/5xx error rate | `sum(rate(student_api_http_requests_total{status=~"4..|5.."}[5m]))` |
| Approximate P95 latency | `histogram_quantile(0.95, sum by (le) (rate(student_api_http_request_duration_seconds_bucket[5m])))` |
| Can Prometheus scrape the API? | `up{job="student-result-api"}` |

Metrics are cumulative counters. Use `rate()` or `increase()` to analyze behavior over time. P95 latency may have no value until enough histogram observations are collected.

## 13. Start Grafana and connect Prometheus

```bash
docker run -d \
  --name grafana \
  --network mlops-monitoring \
  -p 3000:3000 \
  grafana/grafana
```

Open [Grafana](http://localhost:3000). Sign in using the credentials configured for your Grafana instance; change default credentials if applicable. Add a **Prometheus** data source with URL:

```text
http://prometheus:9090
```

Because the containers share the `mlops-monitoring` network, use the container name rather than `localhost` for Prometheus. Save and test the data source.

Create a dashboard with panels such as:

| Panel | PromQL | Suggested visualization |
|---|---|---|
| Model Loaded | `student_api_model_loaded` | Stat |
| Total API Requests | `sum(student_api_http_requests_total)` | Stat |
| Requests per Second | `sum(rate(student_api_http_requests_total[1m]))` | Time series |
| Successful Predictions | `sum(student_api_predictions_total{result="success"})` | Stat |
| Client/Server Error Rate | `sum(rate(student_api_http_requests_total{status=~"4..|5.."}[5m]))` | Time series |
| P95 Request Latency | `histogram_quantile(0.95, sum by (le) (rate(student_api_http_request_duration_seconds_bucket[5m])))` | Time series |

## 14. Observe alerts

Open Prometheus **Alerts/Rules** and inspect `StudentAPIClientErrors` and `StudentAPIDown`. Generate repeated invalid requests to demonstrate the client-error rule, then wait through the configured evaluation duration. Do not intentionally take down a production service without permission.

Prometheus alert rules evaluate state; email, Slack, Teams, SMS, or other notifications normally require Alertmanager or a Grafana contact point and are outside this practical's required scope.

## 15. Troubleshooting

- **`ModuleNotFoundError: prometheus_client`:** add `prometheus-client` to requirements and rebuild.
- **`/metrics` returns 404:** verify the endpoint exists and the latest image is deployed.
- **Duplicate metric registration:** define metrics once at module level.
- **Prometheus target DOWN:** test the public metrics URL, hostname, HTTPS scheme, and service state.
- **Prometheus configuration error:** check YAML indentation and container mount paths.
- **Alert rules not loaded:** check Prometheus Rules/Status and container logs.
- **Grafana cannot reach Prometheus:** ensure both containers share `mlops-monitoring` and use `http://prometheus:9090`.
- **Dashboard has no data:** test the query in Prometheus, generate requests, and widen the time range.
- **Metrics expose sensitive details:** remove sensitive labels and restrict metrics access in production.
- **Client-error alert does not fire:** verify the expression, generate repeated invalid requests, and wait for the `for` duration.

Stop the local monitoring containers when finished:

```bash
docker rm -f grafana prometheus
```

## 16. Observation checklist

- [ ] Local `/metrics` shows `student_api_*` metrics.
- [ ] `student_api_model_loaded = 1`.
- [ ] A valid prediction increments the success counter.
- [ ] An invalid request increments the 4xx HTTP metric and produces a Practical 11 warning.
- [ ] Docker `/health`, `/predict`, and `/metrics` work.
- [ ] GitHub Actions build/test/publish passes and GHCR has the updated image.
- [ ] Render is live and exposes the updated metrics.
- [ ] Prometheus target `student-result-api` is UP.
- [ ] Grafana dashboard panels display data.
- [ ] The client-error alert can be demonstrated.
- [ ] Logs and metrics can be correlated without exposing student data.

## Result

The Student Result Prediction API exposes operational metrics, Prometheus scrapes the deployed service, Grafana visualizes requests/predictions/errors/latency, and basic alerts identify client errors or service unavailability.

## Transition to Practical 13

The next practical can extend monitoring into Kubernetes deployment and scaling.
