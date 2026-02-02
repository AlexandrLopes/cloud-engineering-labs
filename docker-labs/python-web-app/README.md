# Python Web App (Docker + Compose)

A Flask application containerized demonstrating **Environment Variables** and **Orchestration** with Docker Compose.

## Structure
* `app.py`: Python web server that reads `APP_ENV` from the system.
* `Dockerfile`: Instructions to build the secure container image.
* `docker-compose.yml`: Orchestration file to define ports and config.

## How to Run (The Easy Way)

1.  **Build & Run:**
    Uses `docker-compose` to build the image and start the container with custom variables.
    ```bash
    docker-compose up -d
    ```

2.  **Access:**
    Go to `http://localhost:8080`
    You should see: *"Hello from Production (Alexandre's Lab)"*.

3.  **Cleanup:**
    To stop and remove everything:
    ```bash
    docker-compose down
    ```

## Configuration
You can change the environment without touching the code by editing `docker-compose.yml`:
```yaml
environment:
  - APP_ENV=Staging


