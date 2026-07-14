# Cloud Engineering Labs
[![Automated Security Scan](https://github.com/AlexandrLopes/cloud-engineering-labs/actions/workflows/security-scan.yaml/badge.svg)](https://github.com/AlexandrLopes/cloud-engineering-labs/actions/workflows/security-scan.yaml)

Hands-on Cloud/DevOps portfolio — AWS infrastructure, Terraform, CloudFormation, Docker, and Python automation, solving real infrastructure and cost problems end to end.

Every project here follows the same standard: a decision documented alongside the alternative it wasn't, and the trade-off stated directly rather than implied. Every CI/CD, IaC, and automation project also runs through automated scanning (Trivy) as part of the build.

---

## Flagship: Telephony Infrastructure (SIP / VoIP)

Production-oriented AWS architecture for real-time telephony signaling ingress — delivered as a technical assessment.

| Project | What it solves | Tech Stack |
| :--- | :--- | :--- |
| [**SIP Ingress Infrastructure**](https://github.com/AlexandrLopes/sip-ingress-aws) | Layer 4 NLB (UDP) with source-IP preservation and provider allowlisting, stateless ECS Fargate scaling on active SIP sessions (not CPU), RDS Multi-AZ behind RDS Proxy, private subnets reaching AWS services via VPC Endpoints (no NAT). | `Terraform`, `NLB`, `ECS/Fargate`, `RDS Proxy`, `VPC Endpoints` |

---

## Infrastructure as Code (Terraform)

Provisioning modern, versioned infrastructure — on AWS and locally via Docker.

| Project | What it builds | Tech Stack |
| :--- | :--- | :--- |
| [**AWS 3-Tier Infrastructure**](./infrastructure/aws-3tier-infrastructure) | Self-managed 3-tier stack (Bastion → Backend → PostgreSQL 15) with hand-hardened Linux, real observability (Prometheus/Grafana), and automated S3 backup. | `Terraform`, `EC2`, `PostgreSQL`, `Bash`, `Prometheus` |
| [**Containerized 3-Tier Infrastructure**](./infrastructure/containerized-3tier) | The same 3-tier shape running entirely on local Docker via the Terraform Docker provider — Nginx as the sole entry point, no cloud dependency. | `Terraform`, `Docker`, `Nginx`, `PostgreSQL`, `Prometheus`, `Grafana` |
| [**AWS Production Environment**](./infrastructure/terraform-aws) | Hardened EC2 web server (IMDSv2, encrypted EBS) behind a modular VPC — networking split into a reusable `modules/network` component. | `Terraform`, `AWS VPC`, `EC2`, `S3` |
| [**Remote State Backend**](./infrastructure/remote-backend) | S3 + DynamoDB backend for shared, locked Terraform state — the bootstrap project deployed before anything that references it. | `Terraform`, `S3`, `DynamoDB` |

---

## CI/CD & Platform Engineering

Reducing the distance between `git push` and running infrastructure.

| Project | What it solves | Tech Stack |
| :--- | :--- | :--- |
| [**Automated CI/CD Pipeline**](./infrastructure/cloudformation/automated-cicd-pipeline) | Self-service Source → Build → Deploy pipeline on AWS-native services, so a developer's only job is `git push`. | `CloudFormation`, `CodePipeline`, `CodeBuild`, `IAM` |

---

## Serverless & Event-Driven

Decoupled architectures where the queue or event bus is the shock absorber, not the database.

| Project | What it solves | Tech Stack |
| :--- | :--- | :--- |
| [**Serverless eSIM Order Processor**](./infrastructure/cloudformation/serverless-esim-order-processor) | SQS-buffered, Lambda-batched order processing with a dead-letter queue and CloudWatch alarm — failures are retried or surfaced, never silently dropped. | `CloudFormation`, `SQS`, `Lambda`, `DynamoDB` |
| [**S3 Event Processor & Audit Log**](./infrastructure/s3-lambda-trigger) | Validates every uploaded file by extension and size before processing, with a complete audit trail — including for the files it blocks. | `Terraform`, `Lambda`, `DynamoDB`, `S3 Events` |

---

## Containerization

Building and hardening container images, not just running `docker build`.

| Project | What it demonstrates | Tech Stack |
| :--- | :--- | :--- |
| [**Secure Multi-stage Build**](./docker-labs/secure-multistage-build) | Multi-stage Docker build that strips compilers and build tools from the production image entirely, running under gunicorn. | `Docker`, `Python`, `Multi-stage` |
| [**Environment-Driven Web App**](./docker-labs/python-web-app) | Flask app with Docker Compose orchestration, configured entirely through environment variables — no rebuild needed per environment. | `Docker`, `Python`, `Flask` |

---

## Automation & Auditing (Python / Boto3)

Scripts that answer a specific operational question against a live AWS account.

| Project | What it checks | Tech Stack |
| :--- | :--- | :--- |
| [**Security Group Auditor**](./python-automation/ec2-open-ports) | Flags Security Group rules exposed to the internet — including all-traffic rules and IPv6 ranges. | `boto3` |
| [**IAM User Auditor**](./python-automation/iam-security-auditor) | Three independent signals per user: MFA status, login inactivity, and access key age. | `boto3` |
| [**S3 Security Scanner**](./python-automation/s3_security_scanner) | Flags buckets missing encryption or exposed via public access — and calls out buckets that are both. | `boto3` |
| [**S3 Cleanup Tool**](./python-automation/s3-cleanup-tool) | Cost-optimization script for aging S3 objects — dry-run by default. | `boto3` |
| [**Auto-Remediation Bot**](./security-labs/ec2-auto-remediation) | Event-driven (CloudTrail → EventBridge → Lambda) — the one automation here that acts, not just reports, reverting risky Security Group rules sub-second from creation. | `Terraform`, `Lambda`, `EventBridge` |
| [**IAM MFA Checker**](./infrastructure/cloudformation/cfn-iam-security-checker) | Daily scheduled check for IAM users without MFA, with email alerting. | `CloudFormation`, `Lambda`, `EventBridge`, `SNS` |

---

### About Me
Cloud & DevOps Engineer focused on infrastructure automation, Infrastructure as Code, and CI/CD.
* **Certifications:** AWS Certified Cloud Practitioner (CLF-C02), Google Cloud Cybersecurity.
* **Focus:** AWS, Terraform, Docker, Python, CI/CD, Observability.
* **Languages:** English (C2), Portuguese (Native), Spanish (B2).

---
*Every project's README documents not just what was built, but what was rejected and why — versioned with Git, scanned with Trivy.*
