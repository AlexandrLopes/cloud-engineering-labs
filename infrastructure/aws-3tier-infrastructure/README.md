# AWS 3-Tier Infrastructure

**Production-style 3-tier AWS architecture — network isolation, database hardening, observability, and automated backup, with every trade-off made explicit.**

## 1. Context and Objective

A full 3-tier VPC (Bastion → Backend → Database) provisioned with Terraform, with every layer configured manually via Linux CLI — not just `terraform apply` and done.

The focus is on **operational depth**: hands-on Linux administration, a self-managed relational database, real observability, and a backup process that fails loudly instead of silently. This is deliberately *not* a fully-managed, black-box stack — the goal is to demonstrate the layer of knowledge that sits underneath managed services (RDS, CloudWatch, managed Prometheus), not to replace them by default.

**Out of scope:** application-layer code, CI/CD pipeline for app deployment, multi-region failover.

---

## 2. Architecture Overview

```
Internet
  -> Internet Gateway
  -> [Tier 1] Bastion Host (Public Subnet 10.0.1.0/24) — SSH entry point + monitoring stack
       -> SSH Agent Forwarding
  -> [Tier 2] Backend EC2 (Private Subnet 10.0.2.0/24) — application layer, PostgreSQL client
       -> PostgreSQL :5432
  -> [Tier 3] Database (Private Subnet 10.0.3.0/24) — PostgreSQL 15
```

Outbound internet for the private subnets (package installs, S3 access, backup upload) goes through a **NAT Gateway**.

---

## 3. Compute Layer: EC2, Not a Managed Database

**Decision: PostgreSQL 15 installed and hardened by hand on EC2, not RDS.**

This is the central decision of the project, and it's deliberate: RDS would abstract away exactly what this project sets out to demonstrate — OS-level database installation, systemd service management, manual hardening, and a backup process built from scratch instead of relying on RDS automated snapshots.

**Trade-off accepted:** no automated Multi-AZ failover, no automated minor-version patching, no point-in-time recovery out of the box — all of which RDS provides natively. In a real production system with this exact requirement set (no dedicated ops team, high durability needs), **RDS would be the right call**, and I'd default to it. This project isolates the "what's under the hood" layer on purpose.

**Trade-off summary line:** managed service reduces operational surface but hides the mechanics; self-managed EC2 keeps the mechanics visible at the cost of manual failover and patching.

---

## 4. Network and Egress: NAT Gateway, Not VPC Endpoints

**Decision: NAT Gateway for private-subnet outbound access.**

Unlike a containerized workload pulling images from ECR (see `sip-ingress-aws`, which uses VPC Endpoints for exactly that reason), this stack's outbound needs are simpler: OS package installs (`dnf`), the AWS CLI talking to S3 for backups, and general internet reachability for patching. A NAT Gateway covers all of that with a single resource, versus provisioning and paying for multiple Interface Endpoints (S3, SSM, etc.) for a workload that doesn't have ECR-pull-style traffic.

**Trade-off accepted:** the private subnets do have an outbound path to the internet (via NAT), which is a larger network surface than the VPC-Endpoints-only design in `sip-ingress-aws`. Acceptable here because there's no equivalent of "the container never boots without these endpoints" — SSH-based EC2 access doesn't have that hard dependency.

---

## 5. Network Isolation

**Decision: Security Group chaining — no tier skips a hop.**

- Bastion SG: accepts SSH only from a specific admin IP (`allowed_ssh_cidr`).
- Backend SG: accepts SSH only from the Bastion SG. No direct exposure.
- Database SG: accepts PostgreSQL (5432) only from the Backend SG. Never reachable from the Bastion or the internet directly.

Access is granted **by group, not by IP** — if the Backend EC2's IP changes (stop/start, replacement), the rule stays valid without maintenance.

| Resource | Description |
|----------|-------------|
| VPC | Isolated network (10.0.0.0/16) |
| Public Subnet | Bastion Host + Monitoring Stack |
| Private App Subnet | Backend EC2 |
| Private DB Subnet | Database tier |
| Internet Gateway | Public internet access |
| NAT Gateway | Outbound internet for private subnets |
| IAM Role | EC2 access to S3 without hardcoded credentials |

---

## 6. Hardening

- **No hardcoded credentials:** all AWS API access from EC2 (S3 upload for backups) goes through an **IAM Role**, never static keys.
- **EBS encrypted at rest** on every instance.
- **IMDSv2 enforced** on every instance — mitigates SSRF-style metadata credential theft.

**Trade-off not yet closed:** the database password is currently set inline during setup (`CREATE USER ... WITH ENCRYPTED PASSWORD`). For a real production posture, this would move to **Secrets Manager**, fetched at boot — the same pattern used in `sip-ingress-aws`. Flagging this explicitly rather than pretending it's already solved.

---

## 7. Linux & Database Setup

PostgreSQL 15 installed and configured manually on the Backend EC2 via CLI — not a pre-baked AMI:

```bash
sudo dnf install postgresql15-server -y
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

sudo -u postgres psql -c "CREATE DATABASE appdb;"
sudo -u postgres psql -c "CREATE USER appuser WITH ENCRYPTED PASSWORD 'yourpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;"
sudo -u postgres psql -d appdb -c "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
```

---

## 8. Observability Stack

Prometheus and Grafana deployed via Docker Compose on the Bastion Host, scraping the Backend EC2.

| Component | Role | Port |
|-----------|------|------|
| Node Exporter | Exposes system metrics (CPU, memory, disk) from Backend EC2 | 9100 |
| Prometheus | Scrapes and stores metrics every 15 seconds | 9090 |
| Grafana | Visualizes metrics via Node Exporter Full dashboard (ID 1860) | 3000 |

**Why the monitoring stack sits on the Bastion, not the Backend:** keeps the Backend EC2 focused on the application/database role and avoids the monitoring stack's Docker footprint competing with PostgreSQL for resources on the same instance.

**What this actually catches:** disk filling up before a `pg_dump` fails for lack of space, memory pressure before PostgreSQL starts swapping, and CPU spikes that would otherwise only surface as "the app got slow" with no root cause.

**Gap, stated plainly:** there's no alerting wired yet (Alertmanager, or Grafana alert rules) — today this is a dashboard you have to look at, not a system that pages you. Next step if this went further.

---

## 9. Automated Backup

Daily PostgreSQL backup to S3 via Bash script scheduled with cron:

```bash
# Cron job — runs every day at 2AM UTC
0 2 * * * /tmp/backup_postgres.sh
```

Backup flow:
1. `pg_dump` exports the full database to a `.sql` file.
2. AWS CLI uploads to an S3 bucket via IAM Role (no credentials needed).
3. Local file is removed after successful upload.
4. Script exits with code `1` if the backup fails — no silent data loss.

**Why cron and not EventBridge + Lambda/SSM:** cron matches the "self-managed Linux" scope of this project — it lives on the same box as the database, no extra AWS service to provision. Trade-off: no centralized backup monitoring across a fleet, no retry logic beyond the script's own exit code, and if the instance itself is down, the backup silently doesn't run — there's no external check that it fired.

---

## 10. Risks and Trade-offs (Summary)

**EC2 vs RDS:** manual visibility into every layer, at the cost of automated failover, patching, and point-in-time recovery. Right call for this project's purpose; RDS would be right call for real production with these requirements.

**NAT Gateway vs VPC Endpoints:** simpler for this workload's outbound needs (no ECR pulls); larger network surface than an Endpoints-only design.

**Inline DB password vs Secrets Manager:** not yet closed — flagged as the clear next step, not hidden.

**Cron vs managed scheduler:** matches the self-managed scope; no centralized monitoring of backup execution across instances, and a failed instance means a silently-missed backup window.

**No alerting on the observability stack:** dashboards exist, paging doesn't — yet.

**Single-AZ database:** no Multi-AZ failover (would require moving to RDS or building manual replication — not implemented here).

---

## 11. How to Deploy

```bash
git clone https://github.com/AlexandrLopes/cloud-engineering-labs
cd cloud-engineering-labs/infrastructure/aws-3tier-infrastructure

# Set your IP for Bastion SSH access (never commit this file)
echo 'allowed_ssh_cidr = "YOUR_IP/32"' > terraform.tfvars

terraform init
terraform plan
terraform apply
```

## 12. Accessing the Infrastructure

```bash
ssh-add ~/.ssh/three-tier-key

# Connect to Bastion Host
ssh -A -i ~/.ssh/three-tier-key ec2-user@BASTION_PUBLIC_IP

# From Bastion, connect to Backend
ssh ec2-user@BACKEND_PRIVATE_IP
```

## Tech Stack

* **IaC:** Terraform
* **Cloud:** AWS (VPC, EC2, S3, IAM, NAT Gateway, Key Pair)
* **OS:** Amazon Linux 2023
* **Database:** PostgreSQL 15
* **Scripting:** Bash
* **Scheduler:** cron (cronie)
* **Monitoring:** Prometheus, Grafana, Node Exporter
* **Containers:** Docker, Docker Compose
