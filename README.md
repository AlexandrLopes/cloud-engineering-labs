#  Cloud Engineering Labs

Welcome to my practical Cloud Engineering portfolio.
This repository documents my technical journey in solving real-world infrastructure, security, and cost problems using **AWS**, **Python**, and **Terraform**.

**Automation, Security, and Infrastructure as Code.**

---

##  Python Automation (Boto3)
Scripts focused on **SecOps** and **FinOps** interacting directly with the AWS SDK.

| Project | Problem Solved | Tech Stack |
| :--- | :--- | :--- |
| [**S3 Cost Optimizer**](./python-automation/s3-cleanup-tool) |  **Cost:** Identifies and cleans up old/unused files in S3 Buckets based on age policies. | `boto3`, `datetime` |
| [**EC2 Security Auditor**](./python-automation/ec2-open-ports) |  **Security:** Proactively scans the network for risky open ports (22, 3389) exposed to the internet (`0.0.0.0/0`). | `boto3`, `json` |
| [**IAM Security Auditor**](./python-automation/iam-security-auditor) |  **Identity:** Audits IAM users to detect security gaps like missing MFA or unused credentials. | `boto3`, `csv` |
| [**DynamoDB Logger**](./python-automation/dynamodb-security-log) |  **Data:** A log handler system that programmatically creates NoSQL tables and ingests security alerts. | `boto3`, `NoSQL` |

---

##  Infrastructure as Code (Terraform)
Provisioning modern, versioned, and immutable infrastructure.

| Project | What it builds? | Technical Highlights |
| :--- | :--- | :--- |
| [**AWS Production Environment**](./infrastructure/terraform-aws) | A complete infrastructure stack with **VPC**, **EC2** (bootstrapped with User Data), and **S3**. | `modules`, `variables`, `outputs` |
| | [**S3 Event Processor & Audit**](./infrastructure/s3-lambda-trigger) | Event-driven architecture using **Lambda (Python)** to process S3 uploads. Includes **DynamoDB** for metadata persistence and **SecOps Input Validation** to block malicious files. | `boto3`, `dynamodb`, `iam_roles`, `json_parsing` |

---

###  About Me
Cloud Engineer & Automation and Security Enthusiast.
* **Certifications:** AWS Certified Cloud Practitioner (CLF-C02)
* **Focus:** AWS, Python, Terraform, Security (SecOps).
* **Languages:** English (C2), Portuguese (Native), Spanish (intermediate).

---
*This repository is maintained via local CI/CD and versioned with Git.*