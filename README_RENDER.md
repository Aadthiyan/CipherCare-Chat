Render deployment notes

This repository contains a `render.yaml` that deploys both `cyborgdb` (CyborgDB Docker image) and the `backend` as Docker services in the same Render project. The backend is configured to talk to CyborgDB using the internal service name `http://cyborgdb:8002`.

Quick steps to deploy on Render

1. Commit and push these files to your Git repository.
2. In Render, create a new service by connecting this repository (or import via "New Web Service").
   - Render will read `render.yaml` and create both services automatically.
3. Set required environment variables in Render (Team secrets or service env):
   - `DATABASE_URL` (your database)
   - `CYBORGDB_API_KEY` (if the image requires it)
   - `HUGGINGFACE_API_KEY` and any other keys
4. Verify services are healthy in Render dashboard. Backend logs should show successful requests to `http://cyborgdb:8002`.

Notes & recommendations

- Persistent Storage: `cyborgdb` uses the `disk` configured in `render.yaml` (10GB). Adjust as needed.
- Health Checks: Both services expose `/health` and include Docker `HEALTHCHECK` directives.
- Rolling Deploys: You can keep the existing Python/HTTP backend service in Render while you test this Docker-based backend; remove it after verification.

If you want, I can:
- Add a `.env.render.example` with recommended env vars.
- Update the `upload` scripts to accept `CYBORGDB_BASE_URL` override for remote uploads.
