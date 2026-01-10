# AWS Security Group Auditor

A Python automation tool designed for **Cloud Security (SecOps)**. It proactively scans AWS EC2 Security Groups to identify potentially dangerous misconfigurations.

### The Problem
Leaving sensitive ports (like SSH 22 or RDP 3389) open to the entire internet (`0.0.0.0/0`) is a top vulnerability in Cloud environments. Manual auditing is error-prone and slow.

### The Solution
This script automates the audit process by:
1.  Fetching all Security Groups in the region.
2.  Analyzing Inbound Rules (Ingress).
3.  Flagging any rule that allows traffic from `0.0.0.0/0` on risky ports.

### Tech Stack
* **Python 3**
* **Boto3** (AWS SDK)
* **JSON Parsing** logic

###  Usage
```bash
pip install boto3
python main.py
