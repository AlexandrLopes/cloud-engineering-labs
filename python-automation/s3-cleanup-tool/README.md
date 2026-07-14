# AWS S3 Automated Cleanup Tool

**Python automation for S3 lifecycle cost control — dry-run by default, with the deletion logic explicit rather than a black-box AWS Lifecycle Rule.**

## 1. Context and Objective

Logs, backups, and temporary files left in S3 indefinitely accumulate storage cost with no ongoing value. AWS Lifecycle Rules solve this natively — this script solves the same problem with logic that's visible and customizable beyond what a declarative Lifecycle Rule config allows (e.g. conditional exceptions, custom logging, integration into a broader script rather than a fire-and-forget bucket policy).

---

## 2. Why a Script Instead of a Native Lifecycle Rule

**Trade-off, stated directly:** for the base case (delete everything older than N days), a Lifecycle Rule is the lower-maintenance, AWS-native answer — no script to run, no credentials to manage outside the bucket policy itself. This script exists to demonstrate the underlying mechanism and to leave room for logic a Lifecycle Rule can't express as easily (custom age calculation, selective exceptions by prefix or tag, structured logging of what was deleted and why). For a real production cleanup need with no custom logic required, the honest recommendation is the native Lifecycle Rule, not this script.

---

## 3. Safety Design: Dry Run by Default

The actual `s3.delete_object` call is commented out in `main.py`. Running the script as-is only prints what *would* be deleted and why — every file's age is evaluated and logged, but nothing is destroyed until the delete line is deliberately uncommented. This is the correct default for a tool whose failure mode is irreversible data loss: the unsafe action requires an explicit, visible code change to activate, not a flag or environment variable that could be set wrong.

---

## 4. Detection Logic

```
For each object in BUCKET_NAME:
    age_days = today - object.LastModified
    if age_days > DAYS_TO_KEEP:
        flag for deletion
    else:
        keep
```

Age is computed directly from the object's `LastModified` timestamp returned by `list_objects_v2` — no separate metadata store, no assumptions beyond what S3 already tracks per object.

---

## 5. Risks and Trade-offs (Summary)

**Single bucket, single pass, no pagination:** `list_objects_v2` returns up to 1,000 objects per call; the script doesn't check for or follow `NextContinuationToken`. On a bucket with more than 1,000 objects, only the first page is evaluated — objects beyond that are silently never considered. Fine for a lab-scale bucket; a real production version needs a pagination loop.

**No versioning awareness:** if the target bucket has versioning enabled, this only evaluates current object versions — old versions of a "deleted" object could still be accumulating cost independently, which this script doesn't address.

**Manual activation required:** the dry-run default is a safety feature, but it also means this isn't a scheduled, hands-off cleanup — someone has to review the dry-run output and consciously flip it to delete mode. No EventBridge schedule or Lambda wrapper here (contrast with `ec2-auto-remediation` or `cfn-iam-security-checker` in this same portfolio, which run unattended on a schedule).

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your AWS credentials
aws configure

# 3. Run the script (dry run — nothing is deleted)
python main.py

# 4. To actually delete: uncomment the s3.delete_object line in main.py, then re-run
```

## Tech Stack

* **Language:** Python 3
* **SDK:** AWS Boto3
* **Service:** Amazon S3
