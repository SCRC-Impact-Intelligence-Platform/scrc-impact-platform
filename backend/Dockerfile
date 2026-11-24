# Build from the repo root: docker build -f backend/Dockerfile .
FROM python:3.12-slim-bookworm

# Pango and a font are needed by WeasyPrint for PDF reports.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY backend /srv/backend
WORKDIR /srv/backend
RUN pip install --no-cache-dir .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
