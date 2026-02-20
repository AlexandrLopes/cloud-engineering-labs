# Cloud Engineering Labs
[![DevSecOps Security Scan](https://github.com/AlexandrLopes/cloud-engineering-labs/actions/workflows/security-scan.yaml/badge.svg)](https://github.com/AlexandrLopes/cloud-engineering-labs/actions/workflows/security-scan.yaml)

Welcome to my practical Cloud Engineering portfolio.
This repository documents my technical journey in solving real-world infrastructure, security, and cost problems using **AWS**, **Python**, **Terraform**, and **DevSecOps** practices.

**Automation, Security, Infrastructure as Code, and Shift-Left Security.**

---

## DevSecOps & CI/CD Pipeline (New)
Implementing **Shift-Left Security** to detect vulnerabilities before deployment.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**Automated Security Pipeline**](.github/workflows/security-scan.yaml) | **Continuous Security:** A GitHub Actions workflow that automatically scans IaC (Terraform) for misconfigurations and Docker images for CVEs using **Trivy**. Blocks the build if Critical vulnerabilities are found. | `GitHub Actions`, `Trivy`, `CI/CD` |

---

## Security Engineering & SOAR
Advanced projects focused on **Automated Remediation** and **Active Defense**.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**Security Auto-Remediation Bot**](./security-labs/ec2-auto-remediation) | **SOAR / Active Defense:** A Serverless bot that detects high-risk Security Group changes (e.g., Port 22 open to 0.0.0.0/0) via **EventBridge** and **instantly revokes** the rule using **Lambda**. Enforces Zero Trust policies automatically. | `Terraform`, `Python`, `EventBridge`, `IAM` |
| [**S3 Data Integrity Pipeline**](./infrastructure/s3-lambda-trigger) | **Data Security:** Event-driven pipeline that validates file integrity (Magic Bytes/Extensions), processes financial data, and creates audit logs in **DynamoDB**. Uses **IAM Least Privilege** and Server-Side Encryption. | `Terraform`, `Lambda`, `DynamoDB`, `S3 Events` |

---

## Infrastructure as Code (Terraform)
Provisioning modern, versioned, and immutable infrastructure.

| Project | What it builds? | Technical Highlights |
| :--- | :--- | :--- |
| [**AWS Production Environment**](./infrastructure/terraform-aws) | A secure infrastructure stack with **VPC**, **EC2**, and **S3**. | **Hardening:** `IMDSv2`, `EBS Encryption`, `Restricted Security Groups` |

---

## Architecture & Best Practices Implemented
Foundational infrastructure design focusing on scalability and team collaboration.

| Component | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**Modular Networking**](./infrastructure/terraform-aws/modules/network) | **Modular Architecture:** Infrastructure is divided into reusable Terraform modules to keep the root code clean, maintainable, and scalable. | `Terraform`, `AWS VPC` |
| [**Remote State Backend**](./infrastructure/remote-backend) | **State Management & Locking:** Terraform state (`.tfstate`) is securely stored in S3, with concurrency managed by DynamoDB to prevent split-brain issues. | `Terraform`, `S3`, `DynamoDB` |

---

## Python Automation (Boto3)
Scripts focused on **SecOps** and **FinOps** interacting directly with the AWS SDK.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**S3 Cost Optimizer**](./python-automation/s3-cleanup-tool) | **FinOps:** Identifies and cleans up old/unused files in S3 Buckets based on age policies to reduce storage costs. | `boto3`, `datetime` |
| [**EC2 Security Auditor**](./python-automation/ec2-open-ports) | **Reporting:** Proactively scans the network for risky open ports (22, 3389) exposed to the internet. | `boto3`, `json` |
| [**IAM Security Auditor**](./python-automation/iam-security-auditor) | **Identity:** Audits IAM users to detect security gaps like missing MFA or unused credentials. | `boto3`, `csv` |

---

## Containerization
Foundations of modern application deployment and isolation.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**Hardened Python Web App**](./docker-labs/python-web-app) | **App Isolation & Security:** Containerizing a Flask application ensuring environment consistency. Includes OS Patching and runs as a Non-Root User to mitigate container breakout risks. | `Docker`, `Python`, `Flask`, `Linux Hardening` |
| [**Secure Multi-stage Build**](./docker-labs/secure-multistage-build) | **Image Optimization & Attack Surface Reduction:** Implementing multi-stage builds to separate the build environment from the runtime. Reduces image size and eliminates system compilers from production, neutralizing secondary malware execution. | `Docker`, `Python`, `Multi-stage` |

---

### About Me
Cloud Engineer & Automation and Security Enthusiast.
* **Certifications:** AWS Certified Cloud Practitioner (CLF-C02)
* **Focus:** AWS, Python, Terraform, Security (SecOps), DevSecOps.
* **Languages:** English (C2), Portuguese (Native), Spanish (intermediate).

---
*This repository is maintained via local CI/CD, protected by Trivy scans, and versioned with Git.*
