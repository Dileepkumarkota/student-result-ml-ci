# Practical 11 — Logging and Error Tracking for Student Result Prediction API

Continuation of Practical 10. This practical adds safe application logging and error tracking to the existing FastAPI service. Keep the same trained model, routes, preprocessing, Dockerfile, GitHub repository, GHCR package, Actions workflow, and Render service. Do not retrain the model.

## Aim

- Log startup/model loading, HTTP requests, predictions, validation failures, and runtime exceptions.
- Use INFO, WARNING, and ERROR levels appropriately.
- Write logs to stdout/stderr so Docker and Render can capture them.
- Add request IDs and response-time measurements.
- Avoid logging student identifiers, credentials, secrets, or complete request payloads.
- Test successful and failed requests, publish the tested image through the existing CI/CD workflow, redeploy on Render, and inspect runtime logs.

## Prerequisites

- The existing FastAPI project and model artifact are present.
- The Practical 9 GitHub Actions workflow can build, test, and publish the image to GHCR.
- The GHCR package and Render Web Service from Practical 10 exist.
- Verify the application's actual listening port and /health route before deployment.

## 1. Configure Python logging

In app.py, add these imports if needed:

    import logging
    import sys
    import time
    import uuid
    from fastapi import Request, HTTPException
    from fastapi.exceptions import RequestValidationError
    from fastapi.exception_handlers import request_validation_exception_handler

Place this configuration near the top of the application, before model loading:

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logger = logging.getLogger("student-result-api")

Log model loading around the existing load statement. Keep the project's current variable and path names:

    try:
        model = joblib.load(MODEL_FILE)
        logger.info("event=model_loaded model_file=%s", MODEL_FILE)
    except Exception:
        logger.exception("event=model_load_failed model_file=%s", MODEL_FILE)
        raise

Do not print the model object or environment secrets.

## 2. Add request/response middleware

Add after the FastAPI app object is created. It logs method, path, status, duration, and request ID:

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                level,
                "event=http_request request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                request_id, request.method, request.url.path,
                response.status_code, duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "event=http_request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
                request_id, request.method, request.url.path, duration_ms,
            )
            raise

## 3. Log FastAPI validation failures

This captures invalid requests that fail before /predict executes, without logging the entire request body:

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        fields = [
            ".".join(str(part) for part in error.get("loc", []))
            for error in exc.errors()
        ]
        logger.warning(
            "event=validation_error path=%s field_locations=%s error_count=%s",
            request.url.path, fields, len(exc.errors()),
        )
        return await request_validation_exception_handler(request, exc)

## 4. Add safe prediction logging

Preserve the existing StudentResultInput schema and all existing preprocessing, feature ordering, encoders, and pipeline logic. Insert logs around existing inference code rather than blindly replacing the endpoint.

    SAFE_INPUT_FIELDS = set()
    # Example only: SAFE_INPUT_FIELDS = {"attendance", "study_hours"}

Inside the existing /predict function, around the current inference logic:

    payload = data.model_dump()  # Use data.dict() for older Pydantic versions.
    safe_input = {
        key: value for key, value in payload.items()
        if key in SAFE_INPUT_FIELDS
    }
    logger.info(
        "event=prediction_request feature_names=%s safe_input=%s",
        sorted(payload.keys()), safe_input,
    )

    # Keep the project's existing preprocessing and prediction logic here.
    prediction = model.predict(input_df)[0]
    logger.info("event=prediction_success prediction=%s", str(prediction))

Wrap the existing prediction operation in try/except and use logger.exception("event=prediction_failed") for unexpected runtime failures. Return a generic error to the client; do not expose stack traces or secrets in the response. Do not log names, registration numbers, emails, phone numbers, passwords, tokens, or full request bodies.

## 5. Test locally

Use the same startup command and port configured by the project. The original practical gives this typical example, but the repository's actual listening port takes precedence:

    uvicorn app:app --host 0.0.0.0 --port 8000

Test:
- GET /health: expect HTTP 200 and an INFO request log.
- GET /docs: confirm Swagger loads.
- Valid POST /predict: use the project's actual request schema; expect HTTP 200 and prediction logs.
- Invalid POST /predict: omit a required field or use a wrong type; expect HTTP 422 and a validation_error warning.
- A nonexistent route such as /not-a-real-route: expect HTTP 404 and a WARNING request log.

Each completed response should include an X-Request-ID header. Logs should include request ID, status, path, and duration.

## 6. Build and test the Docker image

Use the repository's existing Dockerfile and actual application port. Example commands from the practical:

    docker build -t student-result-prediction:practical-11 .
    docker run --rm -p 8000:8000 --name student-result-p11 student-result-prediction:practical-11

In another terminal, test /health, one valid prediction, one invalid prediction, and a missing route. Confirm logs appear on stdout/stderr. Adjust port mapping to match the app inside this repository's image.

## 7. Commit, publish, and redeploy

Commit the logging change to the branch that triggers the existing Practical 9 workflow. Example:

    git add app.py
    git commit -m "Add API logging and error tracking"
    git push

Then:
1. Open [GitHub Actions](https://github.com/Dileepkumarkota/student-result-ml-ci/actions) and confirm checkout, artifact preparation, Docker build, health test, GHCR login, and image push succeed.
2. Confirm the updated image tag in GitHub Packages.
3. Open the existing Render Web Service from Practical 10 and select Manual Deploy to deploy the latest image/reference.
4. Wait for the service to become live and retest /health, /docs, and /predict.
5. Open Render Logs and locate event=model_loaded, a successful health request, successful prediction events, a validation warning for status 422, and a missing-route warning for status 404.

GHCR prerequisite: if publishing fails with permission_denied: write_package, check the package's Manage Actions access and grant Dileepkumarkota/student-result-ml-ci write access. Do not store registry tokens in source code.

## 8. Observation table

| Test | Expected result | Expected log evidence |
|---|---|---|
| Application startup/model load | Service starts | event=model_loaded |
| /health | HTTP 200 | INFO request log, status=200 |
| Valid /predict | HTTP 200 + prediction | prediction_request, prediction_success |
| Invalid /predict | HTTP 422 | validation_error, status=422 |
| Unknown route | HTTP 404 | WARNING request log, status=404 |
| Docker test | Container remains healthy | Events visible in container logs |
| GitHub Actions | Successful workflow | Build, test, and push steps pass |
| Render redeployment | Service live | Startup and request events visible in Render logs |

## 9. Troubleshooting

- No custom logs: confirm logging configuration runs, rebuild the image, and redeploy.
- Duplicate lines: use one logging configuration; force=True can prevent inherited duplicate handlers in a simple lab.
- 422 without warning: check the RequestValidationError handler and application imports.
- Prediction returns 500 after edits: restore the original preprocessing/pipeline and add logs around it instead of rewriting inference.
- Render shows old behavior: manually deploy the latest GHCR image/reference.
- Sensitive values in logs: remove payload logging; log feature names or explicitly approved SAFE_INPUT_FIELDS only.
- Container exits at startup: inspect syntax, imports, model path, and model loading traceback.
- GHCR push denied: verify the repository has write access to the package.

## 10. Evidence and deliverables

Record local model-load and health logs, a Swagger successful prediction, a validation warning for an invalid request, a successful GitHub Actions run and updated GHCR tag, the Render service live after redeployment, Render log entries for 200/422/404 requests, and the public health endpoint response.

Do not include tokens, private registry credentials, real student identifiers, or confidential academic data in screenshots.

## Result

The existing Student Result Prediction API should produce safe logs for startup, requests, prediction events, validation failures, HTTP errors, and runtime exceptions. After local tests, the updated image is published through the existing CI/CD workflow, redeployed on Render, and verified using runtime logs.

## Transition to Practical 12

Practical 12 follows this work by monitoring availability, request count, error rate, latency, resource usage, and API health, then configuring alerts.
