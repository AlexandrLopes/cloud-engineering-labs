# Secure Multi-stage Docker Build

## Overview
This project demonstrates how to build a minimal, highly secure Docker image for a Python application using the Multi-stage build technique. The objective is to drastically reduce the final image size and eliminate unnecessary OS packages that could be leveraged by an attacker.

## Architecture Flow
The Dockerfile is divided into two main stages:
1. **Stage 1 (Builder):** Uses a base image to install system compilers (e.g., `gcc`, `build-essential`) and Python dependencies into an isolated Virtual Environment (`venv`).
2. **Stage 2 (Production):** Uses a fresh, lightweight base image. It only copies the compiled `venv` and the application code from the Builder stage, leaving all the build tools behind.

## Security Measures Implemented
* **Attack Surface Reduction:** By removing compilers and package managers from the final production image, we neutralize the ability of an attacker to download or compile secondary malware if the container is compromised.
* **Least Privilege (Non-Root User):** The application runs under a dedicated, unprivileged user (`appuser`). This mitigates the risk of a "Container Escape" vulnerability, passing strict DevSecOps CI/CD checks (e.g., Trivy DS-0002).
* **Dependency Isolation:** Utilizing a Python `venv` ensures a clean and predictable transfer of dependencies between stages without polluting the global system site-packages.

## Build and Run
To build the secure image locally:

```bash
docker build -t secure-multistage-app:latest .
```

To verify the image size reduction and run the container:

```bash
docker images | grep secure-multistage-app
docker run -d -p 8080:8080 secure-multistage-app:latest
```