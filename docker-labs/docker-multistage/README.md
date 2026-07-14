# Secure Multi-stage Docker Build

**Minimal, hardened Python image via multi-stage build — attack surface reduced in the image, and the WSGI server actually used, not just installed.**

## 1. Context and Objective

Build tools (compilers, package managers) present in a production container image are unnecessary attack surface — if the container is ever compromised, they're what an attacker uses to compile or fetch secondary payloads. This project demonstrates removing them from the final image entirely via a multi-stage Docker build, while still using them where they're actually needed (the build stage).

```
Stage 1 (builder): python:3.11-slim + gcc/build-essential -> pip install into /opt/venv
Stage 2 (production): fresh python:3.11-slim -> copies only /opt/venv + app.py -> no build tools at all
```

---

## 2. The Gap This Closes: gunicorn Was Installed, Never Used

**What the earlier version actually had:** `requirements.txt` listed `Flask==3.0.0` and `gunicorn==21.2.0` — both installed into the venv in the builder stage, both copied into the production image. But the Dockerfile's `CMD ["python", "app.py"]` ran `app.run()`, Flask's own development server. The production image paid the size/complexity cost of including gunicorn and never actually ran it — an inconsistency easy to spot by anyone reading both files side by side.

**Fixed:** `CMD` now runs `gunicorn --bind 0.0.0.0:8080 app:app` — the server this image was already built to include is the one that actually serves the app.

**Also cleaned up:** the builder stage's `apt-get install` didn't clear the apt cache afterward (`rm -rf /var/lib/apt/lists/*`). Harmless in practice since the builder stage is discarded entirely and never ships, but added for consistency with the hardening habits used elsewhere in this portfolio.

---

## 3. Multi-stage Build: What Actually Gets Left Behind

The production stage (`FROM python:3.11-slim`, no `AS builder`) never runs `apt-get install gcc build-essential` — it only receives `COPY --from=builder /opt/venv /opt/venv` and the application code. No compiler, no build toolchain, no package manager artifacts beyond what `python:3.11-slim` ships with by default. This is the actual size and attack-surface reduction the project claims — verifiable by comparing `docker history` on the two stages, not just asserted.

---

## 4. Security Measures

* **Attack Surface Reduction:** compilers and build tools exist only in the discarded builder stage.
* **Non-root user:** the app runs as `appuser`, created explicitly and granted ownership of `/app` — not root, and not a default user with broader system permissions.
* **Dependency isolation via venv:** the builder installs into `/opt/venv`, copied wholesale into the production stage — a clean, self-contained dependency set with no reliance on the base image's global site-packages.

---

## 5. Risks and Trade-offs (Summary)

**Dev server vs gunicorn (fixed):** covered in Section 2 — the image now runs what it was already built to include.

**`python:3.11-slim`, not distroless or Alpine:** `slim` removes build tools and many OS packages but is still a fuller base than a distroless or Alpine image would be. The trade-off accepted here is compatibility (slim behaves closer to standard Debian, fewer musl-libc surprises with Python C extensions) over the absolute smallest possible image.

**No HEALTHCHECK:** same gap as `python-web-app` — no built-in liveness signal for an orchestrator to check.

---

## Build and Run

```bash
# Build the image
docker build -t secure-multistage-app:latest .

# Check the size reduction
docker images | grep secure-multistage-app

# Run it
docker run -d -p 8080:8080 secure-multistage-app:latest
```

## Tech Stack

* **Language:** Python 3.11
* **Framework:** Flask
* **WSGI Server:** gunicorn
* **Build Technique:** Docker multi-stage build
