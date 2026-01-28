#  Python Web App on Docker

A simple Flask application containerized using Docker.
This lab demonstrates the fundamental principles of **Containerization**: creating a custom image, managing dependencies, and running an isolated application locally.

##  Structure
* `app.py`: The Python Flask web server.
* `Dockerfile`: Instructions to build the secure container image (Linux Debian Slim + Python).
* `requirements.txt`: Python dependencies.

##  How to Run

1.  **Prerequisites:**
    * Docker Desktop installed and running.

2.  **Build the Image:**
    ```bash
    docker build -t my-python-app .
    ```

3.  **Run the Container:**
    Maps the container's internal port (5000) to the local machine's port (8080).
    ```bash
    docker run -d -p 8080:5000 --name python-lab my-python-app
    ```

4.  **Test:**
    Open your browser at: `http://localhost:8080`
    You should see the Container ID (Hostname).

5.  **Cleanup:**
    To stop and remove the container:
    ```bash
    docker rm -f python-lab
    ```