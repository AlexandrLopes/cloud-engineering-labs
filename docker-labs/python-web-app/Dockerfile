FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY . /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

USER appuser

# Flask's own app.run() is a development server — not meant to serve real
# traffic. gunicorn is the actual WSGI server; app.py's `if __name__ ==
# "__main__"` guard means gunicorn importing `app:app` never triggers the
# dev server at all.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
