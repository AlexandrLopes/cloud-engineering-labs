#  S3 Event Processor & Audit Log

This project implements a **Serverless Event-Driven Architecture** to process files uploaded to S3. It includes a **SecOps layer** to validate files before processing and persists metadata in **DynamoDB** for auditing purposes.

##  Architecture

The workflow follows a reactive pattern:

`User Upload (S3)` ➔ `Trigger (Notification)` ➔ `Lambda (Python)` ➔ `Validation (SecOps)` ➔ `Persistence (DynamoDB)`



### Key Components

* **S3 Bucket:** Acts as the ingestion layer for incoming files (invoices, documents).
* **AWS Lambda (Python 3.9):** The compute layer that processes the event. It uses `boto3` to interact with AWS services.
* **DynamoDB:** NoSQL database used to store an immutable audit log of all uploads (Approved or Blocked).
* **Terraform:** Manages all infrastructure as code, including IAM Roles and Permissions (Least Privilege).

##  Security Features (SecOps)

This service implements **Input Validation** to mitigate common attack vectors:

1.  **File Type Validation:** Only allows specific extensions (`.pdf`, `.txt`, `.csv`, `.json`). Blocks executables (`.exe`) or scripts.
2.  **DoS Protection:** Rejects files larger than **5MB** to prevent Lambda timeouts and cost spikes.
3.  **Audit Trail:** Every action is logged. Blocked files are recorded in DynamoDB with a `block_reason` attribute.

##  How to Deploy

The infrastructure is fully managed by Terraform.

```bash
# 1. Initialize Terraform
terraform init

# 2. Review and Apply
terraform apply
```



