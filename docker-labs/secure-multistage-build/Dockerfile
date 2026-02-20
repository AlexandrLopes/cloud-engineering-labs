# Stage 1: Builder

FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential

COPY requirements.txt .
COPY app.py .

RUN pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Production

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY --from=builder /build/app.py /app/app.py

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8080

CMD ["python", "app.py"]
