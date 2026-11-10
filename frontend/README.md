# SCRC Impact Intelligence — Frontend

Presentation-only Admin Console foundation. No backend API calls, mock backend payloads, or email functionality are implemented.

## Stack

- React 19, TypeScript, Vite 7
- Tailwind CSS 4 (Vite plugin)
- React Router, TanStack Query provider, Lucide icons
- Nginx reverse proxy in the Docker runtime image

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Then open http://127.0.0.1:5173. FastAPI can run separately at http://127.0.0.1:8000.

**API routing contract (for future features):** browser calls `/api/resources`, which Vite forwards to `http://127.0.0.1:8000/resources`; production Nginx does the equivalent. There are currently **no actual API requests** in this frontend.

## Production container

```bash
docker build -t scrc-frontend:dev ./frontend
docker run -p 8080:8080 -e BACKEND_UPSTREAM=http://YOUR_BACKEND_HOST:8000 scrc-frontend:dev
```

For Docker Compose, set `BACKEND_UPSTREAM=http://backend:8000` where `backend` is a resolvable service name. In Kubernetes use an internal Service DNS name. Do not expose FastAPI administrative routes before authorization is implemented.

`nginx/default.conf.template` uses the standard Nginx container envsubst template mechanism, and both proxy layers strip the `/api` prefix.

No automatic deployment, auth, real data, emails, or workflows are included. Configure HTTPS, authorization, network policy and correct upstream settings before production.

## Researchers and Resources CRUD (local development)

The `/researchers` and `/resources` pages now call the actual FastAPI endpoints through the `/api` Vite/Nginx proxy. These pages support list, create, edit, and delete; they refresh TanStack Query caches after mutations.

Start FastAPI from `backend/` with `python -m uvicorn app.main:app --reload`, and Vite from `frontend/` with `npm run dev`. Open `http://127.0.0.1:5173/researchers` or `/resources`. No CORS setting is needed for these same-origin proxy calls.

**Security:** FastAPI CRUD endpoints do not yet require an admin login. Do not expose this instance publicly. For existing records, the UI only permits ORCID changes via deletion/recreation because the backend `ResearcherUpdate` schema does not permit editing ORCID. Prefer deactivation over deletion when records are referenced by publications or attributions.
