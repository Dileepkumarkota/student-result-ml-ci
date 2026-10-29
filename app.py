from pathlib import Path
import logging
import time

import joblib
import pandas as pd
from flask import Flask, Response, jsonify, request, g
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("student-result-api")

app = Flask(__name__)

MODEL_PATH = Path("student_result_model.pkl")
FEATURES = [
    "attendance",
    "internal_marks",
    "assignment_marks",
    "previous_score",
]

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
    "Prediction attempts by result",
    ["result"],
)
MODEL_LOADED = Gauge(
    "student_api_model_loaded",
    "Whether the prediction model loaded successfully",
)


@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_request_metrics(response):
    if request.endpoint != "metrics":
        path = request.url_rule.rule if request.url_rule else "unmatched"
        status = str(response.status_code)
        elapsed = time.perf_counter() - getattr(g, "request_start_time", time.perf_counter())
        HTTP_REQUESTS.labels(request.method, path, status).inc()
        HTTP_REQUEST_DURATION.labels(request.method, path).observe(elapsed)
        logger.info(
            "event=http_request method=%s path=%s status=%s duration_ms=%.2f",
            request.method, path, status, elapsed * 1000,
        )
    return response


def load_model():
    if not MODEL_PATH.exists():
        MODEL_LOADED.set(0)
        raise FileNotFoundError(
            "student_result_model.pkl was not found. Run the training pipeline first."
        )
    try:
        loaded_model = joblib.load(MODEL_PATH)
        MODEL_LOADED.set(1)
        logger.info("event=model_loaded")
        return loaded_model
    except Exception:
        MODEL_LOADED.set(0)
        logger.exception("event=model_load_failed")
        raise


@app.get("/")
@app.get("/health")
def health_check():
    return jsonify({"status": "ok", "service": "student-result-prediction"})


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict():
    data = request.get_json(silent=True)
    if not data:
        PREDICTIONS.labels(result="error").inc()
        return jsonify({"error": "JSON request body is required"}), 400

    missing_fields = [feature for feature in FEATURES if feature not in data]
    if missing_fields:
        PREDICTIONS.labels(result="error").inc()
        return jsonify({
            "error": "Missing required fields",
            "missing_fields": missing_fields,
        }), 400

    try:
        sample = pd.DataFrame([{feature: float(data[feature]) for feature in FEATURES}])
    except (TypeError, ValueError):
        PREDICTIONS.labels(result="error").inc()
        return jsonify({"error": "All feature values must be numeric"}), 400

    try:
        model = load_model()
        prediction_code = int(model.predict(sample)[0])
        prediction = "PASS" if prediction_code == 1 else "FAIL"
        PREDICTIONS.labels(result="success").inc()
        logger.info("event=prediction_success")
        return jsonify({"prediction": prediction, "prediction_code": prediction_code})
    except Exception:
        PREDICTIONS.labels(result="error").inc()
        logger.exception("event=prediction_failed")
        return jsonify({"error": "Prediction failed"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
