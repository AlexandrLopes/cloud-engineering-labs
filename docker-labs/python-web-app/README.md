# Python Web App (Docker + Compose)

**Containerized Flask app demonstrating environment-driven configuration and orchestration — running under a real WSGI server, not the framework's own dev server.**

## 1. Context and Objective

A minimal Flask app that reads its environment name from `APP_ENV`, containerized and orchestrated via Docker Compose, to demonstrate configuration-through-environment-variables (12-factor style) without touching the application code to change behavior per environment.

```
docker-compose.yml -> builds image from Dockerfile -> runs container -> host:8080 -> container:5000
```

---

## 2. The Gap This Closes: "Production" Was Running the Dev Server

**What the earlier version actually had:** `docker-compose.yml` sets `APP_ENV=Production (Alexandre's Lab)`, and the app displays that label in its response — but the Dockerfile's `CMD ["python", "app.py"]` runs Flask's built-in development server (`app.run()`), which Flask's own documentation explicitly says not to use in production: it's single-threaded by default and not hardened for real traffic. Labeling the environment "Production" while running the dev server is the kind of inconsistency worth catching before someone else does.

**Fixed:** `gunicorn` added to `requirements.txt`, and the Dockerfile now runs `gunicorn --bind 0.0.0.0:5000 app:app` instead. `app.py` didn't need to change — its `if __name__ == "__main__"` guard means the dev server code path is simply never reached when gunicorn imports the `app` object directly.

**Also cleaned up:** the Dockerfile previously ran `pip install -r requirements.txt` twice — once before upgrading `pip`/`setuptools`/`wheel`, once after. The first install was redundant work with no effect on the final image; removed.

---

## 3. Configuration via Environment Variable

`app.py` reads `APP_ENV` via `os.getenv('APP_ENV', 'Development')` — the same image runs differently depending on what `docker-compose.yml` (or `docker run -e`) sets, without any code change or rebuild. This is the core 12-factor principle this lab demonstrates: configuration lives outside the code.

---

## 4. Hardening

* **Non-root user:** the app runs as `appuser`, not root.
* **Minimal base image:** `python:3.9-slim`.
* **OS packages updated at build time** (`apt-get update && apt-get upgrade -y`), with the apt cache cleared in the same layer to avoid bloating the image.

---

## 5. Risks and Trade-offs (Summary)

**Dev server vs WSGI server (fixed):** covered in Section 2 — the container now runs something actually suitable for real traffic, matching the "Production" label it displays.

**No health check defined:** the container has no `HEALTHCHECK` instruction — Docker Compose or an orchestrator wouldn't know if the app hung without an external check. Fine for a local lab; a gap if this were deployed behind something expecting container-level health signals.

**Single worker by default:** gunicorn's default worker count (1) is fine for a demo; a real deployment would size `--workers` to available CPU.

---

## How to Run

```bash
# Build & run
docker-compose up -d

# Access
# http://localhost:8080

# Cleanup
docker-compose down
```

## Configuration

Change the environment without touching the code, via `docker-compose.yml`:

```yaml
environment:
  - APP_ENV=Staging
```

## Tech Stack

* **Language:** Python 3.9
* **Framework:** Flask
* **WSGI Server:** gunicorn
* **Orchestration:** Docker Compose
