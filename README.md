# Cloud Engineering Labs

Welcome to my practical Cloud Engineering portfolio.
This repository documents my technical journey in solving real-world infrastructure, security, and cost problems using **AWS**, **Python**, and **Terraform**.

**Automation, Security, and Infrastructure as Code.**

---

## Security Engineering & SOAR
Advanced projects focused on **Automated Remediation** and **Active Defense**.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**Security Auto-Remediation Bot**](./security-labs/ec2-auto-remediation) | **SOAR / Active Defense:** A Serverless bot that detects high-risk Security Group changes (e.g., Port 22 open to 0.0.0.0/0) via **EventBridge** and **instantly revokes** the rule using **Lambda**. Enforces Zero Trust policies automatically. | `Terraform`, `Python`, `EventBridge`, `IAM` |
| [**S3 Data Integrity Pipeline**](./infrastructure/s3-lambda-trigger) | **Data Security:** Event-driven pipeline that validates file integrity (Magic Bytes/Extensions), processes financial data, and creates audit logs in **DynamoDB**. Uses **IAM Least Privilege**. | `Terraform`, `Lambda`, `DynamoDB`, `S3 Events` |

---

## Infrastructure as Code (Terraform)
Provisioning modern, versioned, and immutable infrastructure.

| Project | What it builds? | Technical Highlights |
| :--- | :--- | :--- |
| [**AWS Production Environment**](./infrastructure/terraform-aws) | A complete infrastructure stack with **VPC**, **EC2** (bootstrapped with User Data), and **S3**. | `modules`, `variables`, `outputs` |

---

## Python Automation (Boto3)
Scripts focused on **SecOps** and **FinOps** interacting directly with the AWS SDK.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**S3 Cost Optimizer**](./python-automation/s3-cleanup-tool) | **FinOps:** Identifies and cleans up old/unused files in S3 Buckets based on age policies. | `boto3`, `datetime` |
| [**EC2 Security Auditor**](./python-automation/ec2-open-ports) | **Reporting:** Proactively scans the network for risky open ports (22, 3389) exposed to the internet. | `boto3`, `json` |
| [**IAM Security Auditor**](./python-automation/iam-security-auditor) | **Identity:** Audits IAM users to detect security gaps like missing MFA or unused credentials. | `boto3`, `csv` |

---


## Containerization & DevOps
Foundations of modern application deployment and isolation.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**Python Web App Container**](./docker-labs/python-web-app) | **App Isolation:** Containerizing a Flask application to ensure environment consistency ("It works on my machine") using Docker best practices. | `Docker`, `Python`, `Flask`, `Linux` |

---

### About Me
Cloud Engineer & Automation and Security Enthusiast.
* **Certifications:** AWS Certified Cloud Practitioner (CLF-C02)
* **Focus:** AWS, Python, Terraform, Security (SecOps).
* **Languages:** English (C2), Portuguese (Native), Spanish (intermediate).

---
*This repository is maintained via local CI/CD and versioned with Git.*