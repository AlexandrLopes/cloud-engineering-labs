# Stage 1 - Builder
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --target=/app/libs

# Stage 2 - Production
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --shell /bin/false appuser

WORKDIR /app
COPY --from=builder /app/libs /app/libs
COPY app.py .

ENV PYTHONPATH=/app/libs

USER appuser

EXPOSE 8080
CMD ["python3", "app.py"]