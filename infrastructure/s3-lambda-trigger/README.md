# S3 Event Processor & Audit Log

**Serverless, event-driven file ingestion pipeline — every upload validated, every outcome audited, with every trade-off made explicit.**

## 1. Context and Objective

Files land in an S3 bucket (invoices, documents) and need to be validated and processed automatically, with a complete audit trail — including for the files that get rejected, not just the ones that succeed.

```
User Upload (S3) -> S3 Event Notification -> Lambda (Python) -> Validation -> DynamoDB (audit log)
```

---

## 2. Validation: Extension Allowlist and Size Limit

**Decision: allowlist four extensions, reject everything else.**

`.pdf`, `.txt`, `.csv`, `.json` are accepted; anything else — including executables and scripts — is blocked before download. The check runs against the file name from the S3 event itself, so a rejected file is never even pulled into the Lambda's `/tmp`.

**Decision: reject files over 5MB, checked before download.**

The size comes from the S3 event metadata (`record['s3']['object']['size']`), so an oversized file is blocked without ever being downloaded — the check that actually prevents the Lambda timeout / cost-spike scenario it's meant to guard against, rather than downloading first and checking after.

---

## 3. Audit Trail: Every Outcome Recorded, Not Just Successes

**The gap this closes:** the earlier version of this Lambda only wrote to DynamoDB on successful processing. A blocked file returned a `403` and exited — no record, anywhere, of what was blocked or why. That directly contradicted the point of having an audit log.

**Fixed:** every blocked file — wrong extension or oversized — now writes a `BLOCKED` record to DynamoDB with a `block_reason` field describing exactly why (e.g. `"Unsupported file type: malware.exe"` or `"File exceeds size limit: 8388608 bytes (max 5242880)"`). Successful files still write a `PROCESSED` record with the parsed totals. The audit table now reflects everything that happened to the bucket, not just the happy path.

---

## 4. Processing: CSV Gets Analysis, Other Types Get Audited

Only `.csv` files are parsed for a numeric total (summing an `amount` column, if present). `.pdf`, `.txt`, and `.json` pass validation and get an audit record, but there's no numeric analysis defined for them yet — they're accepted and logged, not analyzed. Extending analysis to other formats would need format-specific parsing, not implemented here.

---

## 5. Security Considerations

* **No hardcoded credentials:** Lambda's IAM role grants exactly `dynamodb:PutItem`/`UpdateItem` on the audit table, `sns:Publish` on the specific alert topic, and `s3:GetObject` scoped to the ingestion bucket — nothing broader.
* **Encryption at rest:** the S3 bucket enforces `AES256` server-side encryption by default; the SNS topic uses the AWS-managed KMS key (`alias/aws/sns`).
* **Public access blocked:** all four S3 Block Public Access settings enabled on the bucket.
* **No PII in source:** the alert email is now a placeholder default (`changeme@example.com`) that must be overridden per deployment via `terraform.tfvars` — an earlier version of this file had a real personal email hardcoded as the default, which is a real thing to check for in any public IaC repo, not just this one.

---

## 6. Risks and Trade-offs (Summary)

**Extension allowlist vs content inspection:** blocks by file extension, not by inspecting actual file content (magic bytes) — a renamed malicious file with an allowed extension would pass the extension check. A stronger version would validate magic bytes, not just the name.

**Size check on event metadata:** trusts the size reported by the S3 event rather than a post-download verification — correct for the DoS-prevention goal (never download an oversized file), but means the check relies on S3's own reporting rather than an independent measurement.

**CSV-only analysis:** other allowed formats are audited but not analyzed — acceptable for the current scope, a real gap if this grew into a general document pipeline.

**Single-record event assumption:** the handler reads `event['Records'][0]` — it processes only the first record of an S3 event notification. S3 can deliver multiple records in a single event under some conditions; this handler would silently ignore any records beyond the first.

---

## How to Deploy

```bash
terraform init
terraform apply
```

Set your own alert email before applying:
```bash
echo 'alert_email = "your.email@example.com"' > terraform.tfvars
```

## Tech Stack

* **Infrastructure as Code:** Terraform
* **Ingestion:** Amazon S3 (event notification)
* **Compute:** AWS Lambda (Python 3.9)
* **Storage:** Amazon DynamoDB (`PAY_PER_REQUEST`)
* **Alerting:** Amazon SNS
