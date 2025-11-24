# AWS IAM Inactive User Auditor

This project is a Python script designed to enhance **Cloud Security Posture**. It automatically audits AWS Identity and Access Management (IAM) users to identify dormant accounts that may pose a security risk.

### The Problem
In cloud environments, old or unused accounts ("Zombie Accounts") are a major security vulnerability. If an employee leaves or a service is deprecated, but the IAM user remains active, it increases the attack surface for potential breaches.

### The Solution
This tool scans the AWS account and flags users who:
1. Have not logged in for more than **90 days** (Configurable).
2. Have created an account but **never logged in**.

### Technologies
* **Language:** Python 3
* **SDK:** AWS Boto3
* **Focus:** Security & Compliance (Identity Management)

### How it works
The script utilizes the `boto3` client to fetch user metadata. It calculates the delta between `datetime.now()` and `PasswordLastUsed`.

### How to run
```bash
# 1. Install dependencies
pip install boto3

# 2. Configure AWS Credentials (if not already set)
aws configure

# 3. Run the audit
python main.py
