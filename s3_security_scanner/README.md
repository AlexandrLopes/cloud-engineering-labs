# AWS S3 Security Scanner

> **Automated Cloud Security Auditing Tool (SecOps)**

##  About the Project
This project simulates a **Cloud Security Posture Management (CSPM)** tool. Its goal is to scan AWS storage resources (S3 Buckets) to identify insecure configurations that violate compliance standards (such as GDPR).

The primary focus is detecting **missing Encryption at Rest**, one of the most critical vulnerabilities in cloud environments.

## Features
* **Automated Auditing:** Efficient scanning of resource lists (JSON/Dictionaries).
* **Vulnerability Detection:** Identifies buckets missing Server-Side Encryption (SSE).
* **Compliance Reporting:** Generates a visual terminal output indicating `[OK]` or `[ALERT]` status for each resource.
* **Modular Architecture:** Clear separation between Data, Business Logic, and Execution.

##  Technologies Used
* **Python 3.x**: Core language.
* **Data Structures:** Advanced manipulation of Lists and Dictionaries (mocking AWS API responses).
* **SecOps Logic:** Exception handling and security key validation.

## How to Run
1. Clone this repository.
2. Ensure Python is installed.
3. Run the main script:

```bash
python s3_security_scanner.py
