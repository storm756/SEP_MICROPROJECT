# ---- CityServe Production Container Image ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first for efficient layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and static assets
COPY app.py wsgi.py ./
COPY static ./static

# Security hardening: Run as dedicated non-root user (appuser)
RUN useradd --system --uid 10001 --no-create-home appuser \
    && mkdir -p /data && chown -R appuser:appuser /data
ENV CITYSERVE_DB=/data/cityserve.db
USER appuser
VOLUME /data

EXPOSE 8000

# Automated container healthcheck validating endpoint accessibility
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/categories', timeout=2)"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wsgi:app"]
