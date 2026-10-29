# MLOps Practical 8 — Publish Student Result Prediction to GHCR

## Aim
Publish the already-tested Student Result Prediction Docker image to GitHub Container Registry (GHCR), pull it back, and verify that the model-serving API still works. This step reuses the Practical-7 image; model retraining is not required.

## Prerequisites
- Docker Engine/Desktop running.
- Tested local image (example: `student-result-prediction:latest`; substitute the actual image/tag from Practical-7).
- GitHub account and a Personal Access Token (classic) with `read:packages` and `write:packages`.
- The valid API request used during Practical-7.

## 1. Confirm the local image
```bash
docker images
```

## 2. Authenticate to GHCR
Create a token in GitHub Settings → Developer settings → Personal access tokens → Tokens (classic). Keep it secret; never commit it to the repository or put it in the Dockerfile.

In a POSIX shell, after securely setting `GHCR_TOKEN`:
```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
```
Expected: `Login Succeeded`.

## 3. Tag the tested image
Replace `<github-username>` with the GitHub namespace. Keep the image name lowercase.
```bash
docker tag student-result-prediction:latest ghcr.io/<github-username>/student-result-prediction:v1
docker tag student-result-prediction:latest ghcr.io/<github-username>/student-result-prediction:latest
docker images
```

## 4. Push both tags
```bash
docker push ghcr.io/<github-username>/student-result-prediction:v1
docker push ghcr.io/<github-username>/student-result-prediction:latest
```
A successful push reports the uploaded layers and image digest.

## 5. Verify the package
On GitHub, open the profile/organization → Packages → `student-result-prediction`. Confirm owner and tags. New packages are private by default; change visibility only if public access is intended.

## 6. Pull and run the published image
```bash
docker pull ghcr.io/<github-username>/student-result-prediction:v1
docker run -d --name student-result-from-ghcr -p 8000:8000 ghcr.io/<github-username>/student-result-prediction:v1
docker ps
```

## 7. Re-test the API
If the application has a health endpoint:
```bash
curl http://localhost:8000/health
```
If FastAPI Swagger UI is enabled, visit http://localhost:8000/docs and submit the same valid prediction request used in Practical-7. Preserve the endpoint, port, and JSON schema from the working application; these examples may need adjustment.

## 8. Inspect and clean up
```bash
docker inspect ghcr.io/<github-username>/student-result-prediction:v1
docker stop student-result-from-ghcr
docker rm student-result-from-ghcr
docker logout ghcr.io
```

## Troubleshooting
- **Unauthorized/denied on push:** verify username, token expiry, and `write:packages`.
- **Private image cannot be pulled:** authenticate with `read:packages`.
- **Tag not found:** use `docker images` to confirm the source image name and tag.
- **Port 8000 already used:** try `-p 8001:8000`.
- **Container exits:** inspect `docker logs student-result-from-ghcr`.
- **Prediction validation error:** reuse the exact endpoint and request body from Practical-7.

## Security and MLOps notes
- Never commit credentials or tokens to code, images, screenshots, or reports.
- Publish only an image that passed local functional testing.
- Use versioned tags such as `v1` alongside `latest`; record the digest for reproducibility.
- For CI/CD, prefer GitHub Actions with `GITHUB_TOKEN` and explicit package write permissions.
- Do not retrain the model for this registry step.

## Deliverables checklist
- [ ] `docker images` shows local image and GHCR tags
- [ ] Successful login (no token visible)
- [ ] Successful push output and digest
- [ ] GHCR package and tag visible on GitHub
- [ ] Successful pull and running container
- [ ] Successful health/API prediction test
- [ ] Observation notes with image name, tag, and verification status

**Note:** Replace all placeholders and sample endpoints with the exact values from your Practical-7 setup.
