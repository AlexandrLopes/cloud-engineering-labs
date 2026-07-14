# AWS S3 Security Scanner

**Cloud Security Posture Management (CSPM) check for S3 — real API calls against real buckets, flagging both missing encryption and public exposure.**

## 1. Context and Objective

Two of the most critical S3 misconfigurations are missing encryption at rest and unintended public exposure — and the combination of both on the same bucket is the worst case, not two separate medium risks. This scans every bucket in an account and flags each condition independently, with the combination called out as critical.

---

## 2. The Gap This Closes: Simulated Data, Not a Real Scanner

**What the earlier version actually did:** operated entirely on a hardcoded Python list mimicking an AWS API response — it never called AWS. `requirements.txt` listed `boto3` as a dependency the code never imported, and the documented run command (`python s3_security_scanner.py`) didn't match the actual file (`main.py`).

**Fixed:** the script now calls `list_buckets`, `get_bucket_encryption`, and `get_public_access_block` directly against a real AWS account. `requirements.txt` matches what's actually imported, and the run instructions below match the actual filename.

---

## 3. The Second Gap: Public Exposure Was Collected, Never Evaluated

**What the earlier version actually did:** the mocked dataset included a `Public` field per bucket, but `audit_bucket()` only ever checked `Encryption` — the public-exposure data was present in the input and completely ignored in the logic. A bucket that was both public and unencrypted (the worst-case combination, and present in the original mock data) was reported the same as any other unencrypted bucket, with no distinction.

**Fixed:** `get_public_access_block` is checked per bucket. A bucket with no Public Access Block configuration at all is treated as a potential exposure (not skipped) — the absence of a blocking configuration means nothing is actively preventing public access, which is the correct default assumption for a security check, not an optimistic one.

---

## 4. Severity Logic

Each bucket lands in one of four states, evaluated independently rather than collapsed into a single pass/fail:

| Encrypted | Public | Result |
|---|---|---|
| No | Yes | `CRITICAL` — both conditions at once |
| No | No | `ALERT` — missing encryption |
| Yes | Yes | `ALERT` — exposed despite encryption |
| Yes | No | `OK` |

---

## 5. Risks and Trade-offs (Summary)

**Bucket-level only, not object-level ACLs:** `get_public_access_block` reflects the bucket's own block configuration, not individual object ACLs that could still expose specific objects even under a compliant bucket-level setting — a full audit would need `get_bucket_acl` per object, not implemented here.

**No cross-account bucket policy analysis:** a bucket could be "not public" by AWS's public-access definition but still be shared broadly via a permissive bucket policy granting access to other accounts — this scanner doesn't parse bucket policies, only the Block Public Access configuration.

**Read-only, no remediation:** this reports; it doesn't enable encryption or apply a Block Public Access configuration automatically. Consistent with `ec2-open-ports` and `iam-security-auditor` in this same portfolio — all three are audit tools, not auto-remediation (that pattern lives in `ec2-auto-remediation`).

**Required permissions:** `s3:ListAllMyBuckets`, `s3:GetEncryptionConfiguration`, `s3:GetBucketPublicAccessBlock` — read-only, no write access needed to run this audit.

---

## How to Run

```bash
pip install -r requirements.txt
aws configure
python main.py
```

## Tech Stack

* **Language:** Python 3
* **SDK:** AWS Boto3
* **APIs used:** `s3:ListBuckets`, `s3:GetBucketEncryption`, `s3:GetPublicAccessBlock`
