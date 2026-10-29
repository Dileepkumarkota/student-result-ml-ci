# Run graphs in Docker — Student Result Prediction

This repository now includes a local Docker monitoring stack using Flask Prometheus metrics, Prometheus, and Grafana.

## Start everything

Prerequisites: Docker Desktop (with Docker Compose) and Python installed. From the repository root, run:

```bash
python -m pip install -r requirements.txt
python train_model.py
docker compose -f docker-compose.monitoring.yml up --build -d
```

The training command generates the model artifacts that the existing Dockerfile copies into the image. Run it before building the API image.

## Open the services

- **Grafana graphs/dashboard:** http://localhost:3000
- **Prometheus targets and query browser:** http://localhost:9090/targets
- **Student API health:** http://localhost:5000/health
- **API metrics:** http://localhost:5000/metrics
- **API docs:** this project uses Flask, so it does not provide FastAPI Swagger at `/docs` by default.

Grafana default local lab login: username `admin`, password `admin`. Change this password for any non-local or shared deployment. This compose setup binds the dashboards to local development ports and is not intended to expose Grafana to the public internet.

## Make the graphs move

Prometheus scrapes the API every 5 seconds. Generate traffic in PowerShell or a terminal:

```powershell
1..20 | ForEach-Object {
  Invoke-RestMethod http://localhost:5000/health | Out-Null
}
```

Send valid predictions to increase the prediction counter (use the actual expected feature fields):

```powershell
$body = @{
  attendance = 85
  internal_marks = 78
  assignment_marks = 90
  previous_score = 72
} | ConvertTo-Json

1..10 | ForEach-Object {
  Invoke-RestMethod -Method Post -Uri http://localhost:5000/predict -ContentType "application/json" -Body $body
}
```

Refresh the Grafana dashboard. Panels are pre-provisioned for request rate, total requests, P95 latency, HTTP error rate, successful predictions, and model-loaded status. Metrics may take a few scrape intervals to appear; latency percentiles need enough requests.

## Troubleshooting

- Check containers: `docker compose -f docker-compose.monitoring.yml ps`
- Follow logs: `docker compose -f docker-compose.monitoring.yml logs -f`
- Stop services: `docker compose -f docker-compose.monitoring.yml down`
- If Docker build says model or metrics artifacts are missing, rerun `python train_model.py` and build again.
- If the Prometheus target is down, open http://localhost:9090/targets and confirm `student-result-api` is UP.
- Do not expose the default Grafana password on a public host. The local Grafana password above is for classroom/demo use only.

## What was added

- `docker-compose.monitoring.yml`: API, Prometheus, Grafana containers.
- `monitoring/prometheus.yml`: scrapes the API metrics endpoint.
- `monitoring/grafana/provisioning/`: automatic Prometheus data source and dashboard provisioning.
- `monitoring/grafana/dashboards/student-result-api.json`: prebuilt graphs.
- `app.py` and `requirements.txt`: Prometheus request, latency, prediction, and model readiness metrics.
