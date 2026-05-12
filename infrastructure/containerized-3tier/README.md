# Containerized 3-Tier Infrastructure

## Overview
A production-style 3-tier infrastructure running entirely on local Docker containers, provisioned with **Terraform** using the Docker provider. Built to demonstrate container orchestration, reverse proxy configuration, and full-stack observability with Prometheus and Grafana — no cloud dependencies required.

## Architecture

**Client** -> **[Tier 1] Nginx** (Reverse Proxy, Port 80) -> **[Tier 2] Application Services** (Grafana :3000 / Prometheus :9090) -> **[Tier 3] PostgreSQL** (Port 5432) + **Node Exporter** (:9100)

All services communicate through an isolated Docker network (`platform-network`).

## Infrastructure (Terraform + Docker Provider)

| Resource | Description |
|----------|-------------|
| docker_network | Isolated bridge network for inter-container communication |
| docker_volume (postgres-data) | Persistent storage for PostgreSQL data |
| docker_volume (grafana-data) | Persistent storage for Grafana dashboards |
| docker_container (postgres) | PostgreSQL 15 database |
| docker_container (prometheus) | Metrics collection every 15 seconds |
| docker_container (grafana) | Metrics visualization |
| docker_container (node-exporter) | System metrics exporter |
| docker_container (nginx) | Reverse proxy — single entry point on port 80 |

## Security Design
* **Reverse proxy as single entry point:** Only port 80 exposed externally via Nginx
* **Isolated network:** All inter-container communication stays inside `platform-network`
* **No hardcoded credentials:** PostgreSQL credentials managed via Terraform variables with `sensitive = true`
* **Least privilege containers:** Services expose only required ports internally

## Observability Stack

| Component | Role | Port |
|-----------|------|------|
| Node Exporter | Exposes system metrics (CPU, memory, disk) | 9100 |
| Prometheus | Scrapes and stores metrics every 15 seconds | 9090 |
| Grafana | Visualizes metrics via Node Exporter Full dashboard (ID 1860) | 3000 |

Prometheus scrape config targets `node-exporter:9100` using Docker DNS resolution — no hardcoded IPs.

## Nginx Reverse Proxy

```nginx
location /grafana/    → proxied to grafana:3000
location /prometheus/ → proxied to prometheus:9090
```

## How to Deploy

```bash
git clone https://github.com/AlexandrLopes/cloud-engineering-labs
cd cloud-engineering-labs/infrastructure/containerized-3tier

terraform init
terraform plan
terraform apply
```

## Accessing the Stack

| Service | URL |
|---------|-----|
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Nginx (reverse proxy) | http://localhost:80 |
| PostgreSQL | localhost:5432 |

## Teardown

```bash
terraform destroy
```

> **Note:** Running `terraform destroy` will delete all volumes including PostgreSQL data. This is expected behavior for a local lab environment.

## Tech Stack
* **IaC:** Terraform (Docker Provider)
* **Containers:** Docker
* **Reverse Proxy:** Nginx
* **Database:** PostgreSQL 15
* **Monitoring:** Prometheus, Grafana, Node Exporter