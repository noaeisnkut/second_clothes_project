# Infrastructure

This directory contains the Docker Compose setup for the 3-tier application, including the Flask backend, MySQL database, and test container.

## Services

### Flask App
- **Container Name:** `flask_app`
- **Image:** `noa10203040/flask_app:latest`
- **Ports:** `5000:5000`
- **Volumes:** `./static/uploads:/app/static/uploads`
- **Env File:** `pass_env1`
- **Depends on:** MySQL service (waits until healthy)

### MySQL
- **Container Name:** `mysql`
- **Image:** `mysql:latest`
- **Env File:** `db/cred.env`
- **Volumes:** `mysql-data:/var/lib/mysql`
- **Healthcheck:** Ensures the database is ready before dependent services start

### Test Service
- **Container Name:** `test_app`
- **Image:** `noa10203040/test:latest`
- **Depends on:** `flask_app` and `mysql`
- **Env File:** `pass_env1`
- **Volumes:** `. : /app`
- **Command:** runs `pytest` on `app_test.py`

---

## How to Run

From the root of the project:

```bash
docker-compose -f infra/docker-compose.yml up -d
