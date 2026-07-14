# STAGE 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
COPY app.py .

RUN pip install --no-cache-dir -r requirements.txt


# STAGE 2: Production
FROM python:3.11-slim

RUN useradd -m -s /bin/bash appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/app.py /app/app.py

RUN chown -R appuser:appuser /app

USER appuser

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8080

# gunicorn was already in requirements.txt and installed into the venv, but
# the command still ran `python app.py` — Flask's dev server, not gunicorn.
# This is what "Production" stage should have been running all along.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
