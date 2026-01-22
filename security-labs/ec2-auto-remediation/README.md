# AWS Security Auto-Remediation Bot (SOAR)

**Automated Incident Response for Security Group Misconfigurations.**

## Overview
In Cloud Security, **exposure time** is critical. A Security Group rule opening port 22 (SSH) or 3389 (RDP) to the entire internet (`0.0.0.0/0`) can lead to a brute-force compromise in minutes.

This project implements a **Serverless SOAR (Security Orchestration, Automation, and Response)** solution. It acts as an autonomous "security guard" that actively listens for risky network changes and instantly reverts them, enforcing a **Zero Trust** posture.

---

## Architecture

The solution uses an **Event-Driven Architecture** to ensure near real-time remediation (sub-second response).

```mermaid
graph LR
    A[User/Attacker] -- Creates Risky Rule --> B[AWS CloudTrail]
    B -- Triggers Event --> C[Amazon EventBridge]
    C -- Invokes --> D[AWS Lambda (Python)]
    D -- 1. Analyzes JSON --> D
    D -- 2. Detects 0.0.0.0/0 on Port 22/3389 --> D
    D -- 3. RevokeSecurityGroupIngress API --> E[EC2 Security Group]
    E -- Rule Deleted --> F[CloudWatch Logs]