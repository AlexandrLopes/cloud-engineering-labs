# Serverless IAM Security Checker (CloudFormation Native)

## Overview
An automated, event-driven DevSecOps tool built entirely with **AWS CloudFormation**. It provisions a serverless architecture to perform daily compliance audits on AWS IAM users, identifying accounts lacking Multi-Factor Authentication (MFA) and notifying the Security Team in real-time.

## Architecture
This project implements Infrastructure as Code (IaC) using AWS-native services:
* **AWS CloudFormation:** Acts as the orchestrator to deploy the entire stack dynamically.
* **Amazon EventBridge:** Triggers the audit daily (cron schedule).
* **AWS Lambda (Python/Boto3):** Executes the audit logic (CIS Benchmark compliance).
* **Amazon SNS:** Dispatches email alerts to the SecOps team.
* **AWS IAM Role:** Enforces strict **Least Privilege** execution.

## Security & Compliance (Trivy Ready)
* **Zero Hardcoded Credentials:** The Python code relies entirely on the IAM execution role provided by the CloudFormation template.
* **Least Privilege:** The Lambda role is highly restricted. It can only execute `iam:ListUsers` and `iam:ListMFADevices`, and is strictly confined to publishing only to the specific SNS Topic ARN created in the stack.
* **CIS Benchmark Alignment:** Directly addresses Identity and Access Management standards by enforcing MFA tracking.

## How to Deploy
You can deploy this entire stack using the AWS CLI. Be sure to provide your email address to receive the alerts.

```bash
aws cloudformation create-stack \
  --stack-name iam-security-audit-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=AlertEmail,ParameterValue=your.email@example.com \
  --capabilities CAPABILITY_IAM