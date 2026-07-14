# Remote State Backend

**S3 + DynamoDB Terraform state backend — encrypted, versioned, lockable, and deliberately built to be deployed before anything that depends on it.**

## 1. Context and Objective

Terraform state stored locally (`terraform.tfstate` on disk) doesn't work once more than one person or one machine touches the same infrastructure — no locking, no shared source of truth, and a lost laptop means a lost state file. This project provisions the S3 bucket (state storage) and DynamoDB table (state locking) that other projects in this portfolio point their `backend "s3"` block at.

---

## 2. The Bootstrap Problem, Stated Explicitly

**Why this project uses local state for itself:** it can't use a remote backend to provision the very backend it's creating — a chicken-and-egg problem inherent to any "backend as code" setup. This project is deployed once, with local state, specifically to create the bucket and table that `terraform-aws` (and any future project) then references in its own `backend "s3"` configuration.

**Deploy order this implies:**
1. `remote-backend` first — local state, creates `alexandre-labs-terraform-state-2026` (S3) and `terraform-state-locks` (DynamoDB).
2. `terraform-aws` (or any other project pointing at this backend) second — its `backend "s3"` block references the exact bucket/table names created in step 1.

This dependency isn't enforced by Terraform itself — it's an operational sequencing fact that has to be known, not something `terraform apply` would catch if run out of order. Stating it here rather than assuming it's obvious.

---

## 3. State Storage Hardening

* **Versioning enabled** on the state bucket — a corrupted or bad state push doesn't destroy history; previous versions are recoverable.
* **`AES256` encryption** by default on the bucket.
* **All four Block Public Access settings enabled** — a Terraform state file often contains sensitive values (see the note on `sip-ingress-aws`'s RDS password ending up in state); it should never be one misconfiguration away from being public.
* **`force_destroy = true`:** deliberately set for this lab context, so the bucket can be torn down without manually emptying every state version first. **Trade-off stated directly:** this would be the wrong setting for a real shared-team backend, where accidental `terraform destroy` should not be able to take the state bucket down with it.

---

## 4. State Locking

`aws_dynamodb_table.terraform_locks` uses `LockID` as the hash key — the schema Terraform's S3 backend expects for native locking. `PAY_PER_REQUEST` billing avoids provisioning fixed capacity for what's typically light, bursty traffic (a lock write per `apply`/`plan`). Point-in-time recovery and encryption are both enabled on the table.

---

## 5. Risks and Trade-offs (Summary)

**`force_destroy = true`:** convenient for a lab environment that gets torn down and rebuilt; the wrong default for a real multi-person backend where the state bucket should be one of the hardest things in the account to accidentally delete.

**No cross-region replication:** the state bucket is single-region. A regional S3 outage would block `terraform apply`/`plan` for anything using this backend — acceptable for a lab, a real consideration for critical infrastructure state.

**Manual bootstrap order:** as covered in Section 2, nothing enforces "deploy this before anything that references it" except documentation — a `terraform init` against a backend that doesn't exist yet fails immediately and obviously, so the failure mode is loud, not silent, but it's still a manual sequencing step to know about.

---

## How to Deploy

```bash
terraform init
terraform plan
terraform apply
```

Deploy this **before** any project that references this backend's bucket/table in its own `backend "s3"` block.

## Tech Stack

* **IaC:** Terraform (local state, by design — see Section 2)
* **State Storage:** Amazon S3 (versioned, encrypted, public access blocked)
* **State Locking:** Amazon DynamoDB (`PAY_PER_REQUEST`, encrypted, PITR enabled)
