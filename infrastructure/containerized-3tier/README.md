# Containerized 3-Tier Infrastructure

**Production-style 3-tier stack on local Docker, provisioned with Terraform — reverse proxy, observability, and persistence, with the security claims actually enforced by the code, not just the README.**

## 1. Context and Objective

The same 3-tier shape as `aws-3tier-infrastructure` (reverse proxy → application/metrics tier → database), running entirely on local Docker containers via Terraform's Docker provider — no cloud dependencies, useful for demonstrating the same architectural thinking without AWS cost or setup.

```
Client -> [Tier 1] Nginx (:80, only externally exposed port)
       -> [Tier 2] Grafana / Prometheus (internal only, reached via Nginx)
       -> [Tier 3] PostgreSQL + Node Exporter (internal only, never exposed)
```

All services communicate over an isolated Docker bridge network (`platform-network`).

---

## 2. The Gap This Closes: "Single Entry Point" Wasn't Actually Enforced

**What the earlier version actually had:** the README's Security Design section claimed Nginx was the only externally exposed service — but the Terraform config published external ports directly for Grafana (`3000`), Prometheus (`9090`), and Node Exporter (`9100`) as well. Anyone on the host could reach Grafana or Prometheus directly, bypassing Nginx entirely — the "single entry point" claim was aspirational, not actual.

**Fixed:** those three containers no longer publish external ports at all. They're reachable only from other containers on `platform-network` — Grafana and Prometheus are accessed exclusively through Nginx's reverse proxy paths (`/grafana/`, `/prometheus/`), and Node Exporter is scraped by Prometheus internally, never reachable from the host. Grafana's `GF_SERVER_ROOT_URL` and `GF_SERVER_SERVE_FROM_SUB_PATH` are set so its own internal links work correctly when served from the `/grafana/` subpath instead of its root.

---

## 3. The Second Gap: A Weak Password Committed in Plaintext

**What the earlier version actually had:** `postgres_password` was marked `sensitive = true` in Terraform — which only suppresses the value from CLI output and plan diffs — but its `default` was `"admin123"`, sitting in plaintext in `variables.tf`, committed to a public repository. `sensitive = true` protected nothing here; the actual secret was visible to anyone who opened the file.

**Fixed:** the variable now has no default at all — it must be supplied via `terraform.tfvars` (gitignored) or `-var` at apply time. Terraform will prompt for it interactively if it's not provided either way, rather than silently falling back to a weak, public value.

---

## 4. Observability Stack

| Component | Role | Reachable from |
|-----------|------|-----------------|
| Node Exporter | Exposes system metrics (CPU, memory, disk) | Internal only (scraped by Prometheus) |
| Prometheus | Scrapes and stores metrics every 15 seconds | Internal only, proxied via `/prometheus/` |
| Grafana | Visualizes metrics via Node Exporter Full dashboard (ID 1860) | Internal only, proxied via `/grafana/` |

Prometheus's scrape config targets `node-exporter:9100` using Docker's internal DNS — no hardcoded container IPs.

---

## 5. Risks and Trade-offs (Summary)

**Single entry point (fixed):** covered in Section 2 — the security claim is now actually what the running stack does, not just what the README said it did.

**Weak default password (fixed):** covered in Section 3 — no secret ships in the repo anymore; the trade-off is a slightly less "just clone and run" experience, which is the correct trade for not publishing credentials.

**Postgres has no external port, by design:** unlike the README's earlier claim of `localhost:5432` access, Postgres is reachable only from other containers on `platform-network`. For local debugging, use `docker exec -it postgres psql -U <user> -d <db>` rather than a host-level client — this is a deliberate least-privilege choice, not an oversight.

**`terraform destroy` deletes all volumes:** Postgres and Grafana data don't survive a teardown. Correct behavior for a local lab, wrong behavior if this pattern were reused for anything meant to persist.

---

## How to Deploy

```bash
git clone https://github.com/AlexandrLopes/cloud-engineering-labs
cd cloud-engineering-labs/infrastructure/containerized-3tier

echo 'postgres_password = "your-own-password-here"' > terraform.tfvars

terraform init
terraform plan
terraform apply
```

## Accessing the Stack

| Service | URL |
|---------|-----|
| Grafana | http://localhost/grafana/ |
| Prometheus | http://localhost/prometheus/ |
| Nginx (reverse proxy, single entry point) | http://localhost:80 |
| PostgreSQL | Internal only — `docker exec -it postgres psql -U <user> -d <db>` |

## Teardown

```bash
terraform destroy
```

> **Note:** deletes all volumes, including PostgreSQL data. Expected behavior for a local lab environment.

## Tech Stack

* **IaC:** Terraform (Docker Provider)
* **Containers:** Docker
* **Reverse Proxy:** Nginx
* **Database:** PostgreSQL 15
* **Monitoring:** Prometheus, Grafana, Node Exporter
