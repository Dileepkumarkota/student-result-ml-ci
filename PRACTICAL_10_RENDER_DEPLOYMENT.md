# Practical 10 — Deploy the GHCR image to Render

This practical continues the Student Result Prediction project from Practical 9. Render should run the **already-tested image from GHCR**; do not retrain the model or rebuild a separate image for this step.

## 1. Prerequisite: Practical 9 must pass

1. Open the [GitHub Actions runs](https://github.com/Dileepkumarkota/student-result-ml-ci/actions).
2. Confirm the latest **Build, Test and Publish Student Result Prediction** run is green.
3. Confirm the package is published at:

   `ghcr.io/dileepkumarkota/student-result-prediction:latest`

If the GHCR push fails with `permission_denied: write_package`, fix the package's **Manage Actions access** to grant `Dileepkumarkota/student-result-ml-ci` write access before continuing.

## 2. Create the Render service

1. Sign in to the [Render Dashboard](https://dashboard.render.com/).
2. Select **New → Web Service** and choose **Existing Image**.
3. Enter the image URL above.
4. If the GHCR package is public, registry credentials usually aren't needed. If private, add a GitHub registry credential using a Personal Access Token (classic) with only `read:packages` access. Never commit or share the token.
5. Name the service `student-result-prediction`, choose an available region and plan, and set the health check path to `/health`.
6. Set the `PORT` environment variable to match the image's configured listening port.

### Important: confirm the port used by this repository

The Practical 9 workflow currently starts the CI container on port **5000** and checks `http://localhost:5000/health`. Use `PORT=5000` on Render **if the application inside the published image actually listens on port 5000**. The Practical 10 classroom document describes port 8000 as its default; do not blindly use 8000 if the image built by this repository uses 5000. The Render port must match the app's actual bind port, and the app must bind to `0.0.0.0`.

7. Create/deploy the service and wait for Render to report it live.

## 3. Verify the public service

Replace `<render-service-name>` with the actual hostname assigned by Render:

- Root: `https://<render-service-name>.onrender.com/`
- Health: `https://<render-service-name>.onrender.com/health`
- Swagger UI: `https://<render-service-name>.onrender.com/docs`
- Prediction: send a `POST` request to `https://<render-service-name>.onrender.com/predict` using the exact validated JSON payload from the earlier practical. Do not invent a new request schema.

Check Render's deployment events and runtime logs if image pull, startup, port binding, health checks, or predictions fail.

## 4. Deploy later GHCR updates

An image-backed Render service may not automatically redeploy when the mutable `latest` tag changes. After Practical 9 publishes a new image, open the Render service and select **Manual Deploy → Deploy latest reference**, then retest the endpoints.

## 5. Record practical evidence

Record the actual Render URL and capture the successful Practical 9 workflow, GHCR `latest` tag, Render image configuration (with secrets hidden), live deployment, root/health/docs/predict checks, and relevant logs.

**Security:** Never place GHCR tokens or Render deploy hooks in this repository, screenshots, or reports.
