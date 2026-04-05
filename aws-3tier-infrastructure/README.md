# AWS 3-Tier Infrastructure

## Overview
A production-style 3-tier architecture on AWS, provisioned entirely with **Terraform** and configured manually via Linux CLI. Built to demonstrate real infrastructure skills: networking, security, database administration, and automated backup with Bash scripting.

## Architecture

**Internet** ➝ **[Tier 1] Bastion Host** (Public Subnet 10.0.1.0/24) ➝ SSH Agent Forwarding ➝ **[Tier 2] Backend EC2** (Private Subnet 10.0.2.0/24) ➝ PostgreSQL port 5432 ➝ **[Tier 3] Database** (Private Subnet 10.0.3.0/24)

## Infrastructure (Terraform)

| Resource | Description |
|----------|-------------|
| VPC | Isolated network (10.0.0.0/16) |
| Public Subnet | Bastion Host |
| Private App Subnet | Backend EC2 |
| Private DB Subnet | Reserved for database tier |
| Internet Gateway | Public internet access |
| NAT Gateway | Outbound internet for private subnets |
| Security Groups | Least privilege — Bastion, Backend, Database |
| IAM Role | EC2 access to S3 without hardcoded credentials |
| Key Pair | SSH authentication |

## Security Design
* **Bastion as single entry point:** Accepts SSH from a specific IP only
* **Layered access control:** Backend accepts SSH exclusively from Bastion SG — Database accepts PostgreSQL (5432) exclusively from Backend SG
* **No hardcoded credentials:** IAM Role used for AWS API access from EC2
* **Encrypted storage:** EBS volumes encrypted at rest on all instances
* **IMDSv2 enforced:** Instance Metadata Service v2 required on all instances

## Linux & Database Setup
PostgreSQL 15 installed and configured manually on the Backend EC2 via CLI:
```bash
# Install and initialize PostgreSQL
sudo dnf install postgresql15-server -y
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

# Create database, user and table
sudo -u postgres psql -c "CREATE DATABASE appdb;"
sudo -u postgres psql -c "CREATE USER appuser WITH ENCRYPTED PASSWORD 'yourpassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;"
sudo -u postgres psql -d appdb -c "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
```

## Automated Backup
Daily PostgreSQL backup to S3 via Bash script scheduled with cron:
```bash
# Cron job — runs every day at 2AM UTC
0 2 * * * /tmp/backup_postgres.sh
```

Backup flow:
1. `pg_dump` exports the full database to a `.sql` file
2. AWS CLI uploads to S3 bucket via IAM Role (no credentials needed)
3. Local file is removed after successful upload
4. Script exits with code `1` if backup fails — preventing silent errors

## How to Deploy
```bash
# Clone the repository
git clone https://github.com/AlexandrLopes/aws-3tier-infrastructure
cd aws-3tier-infrastructure

# Set your IP for Bastion SSH access (never commit this file)
echo 'allowed_ssh_cidr = "YOUR_IP/32"' > terraform.tfvars

# Deploy infrastructure
terraform init
terraform plan
terraform apply
```

## Accessing the Infrastructure
```bash
# Add SSH key to agent
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