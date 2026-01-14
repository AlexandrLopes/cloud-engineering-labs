# Serverless Automation with Terraform & AWS Lambda

This project demonstrates a modern **Infrastructure as Code (IaC)** approach to deploy Serverless functions. Instead of manual uploads, Terraform handles the entire lifecycle: zipping the code, creating IAM roles, and deploying to AWS Lambda.

### Project Structure
* `main.tf`: Defines the infrastructure (Lambda, IAM, Archive provider).
* `lambda_function.py`: The Python logic to be executed.

---

### Technical Deep Dive: Why `source_code_hash`?

You might notice this specific line in the `aws_lambda_function` resource:

```hcl
source_code_hash = data.archive_file.lambda_zip.output_base64sha256
```
--- 

**The Problem:** Terraform is state-aware. If I only change the Python code (logic) but keep the configuration (infrastructure) the same, Terraform might not detect changes and skip the deployment.

**The Solution:** I use a Base64 SHA256 Hash of the zip file.

Terraform calculates the mathematical fingerprint of the zip.

If I change a single character in the Python code, this fingerprint changes completely.

This forces Terraform to recognize a "change" in the infrastructure state, triggering a fresh update of the Lambda function code on AWS.