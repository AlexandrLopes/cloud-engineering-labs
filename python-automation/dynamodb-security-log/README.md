# DynamoDB Security Logger

**Centralized alert store for security findings — every audit and remediation tool in this portfolio writes here.**

## 1. Context and Objective

Every audit and remediation tool in this portfolio (`ec2-open-ports`, `s3_security_scanner`, `ec2-auto-remediation`) currently prints findings to stdout or CloudWatch Logs, with no shared, queryable record across tools. This provides a single DynamoDB table any of them can log into — one place to see "what got flagged, when, how severe."

---

## 2. Table Design

```
Partition Key: alert_id (String)
Sort Key:      timestamp (String)
```

Composite key means multiple alerts can share an `alert_id` over time if needed (e.g. re-flagging the same resource), sorted chronologically per ID. Each item also carries `severity`, `message`, and `status` (defaults to `OPEN`).

**Billing mode: `PAY_PER_REQUEST`, not provisioned capacity.** Every other DynamoDB table in this portfolio (`esim-active-profiles`, `S3_File_Audit_Log`) uses on-demand billing — this one now matches. Provisioned throughput (5 RCU/5 WCU) bills hourly regardless of usage; for a table that logs occasional alerts, that's a fixed cost for no benefit.

**Point-in-time recovery enabled** — consistent with the hardening pattern used on the other stateful resources in this portfolio (e.g. the Terraform state backend's DynamoDB table).

---

## 3. Usage: A Callable Function, Not a Fixed Demo

`log_alert()` takes `severity` and `message` as parameters — it's meant to be imported and called from other scripts (or extended into a Lambda handler other automation invokes), not just run standalone. The CLI entry point (`main()`) exists for manual testing:

```bash
python main.py --severity HIGH --message "Port 22 open to 0.0.0.0/0 on sg-0123456789"
```

Running it repeatedly logs distinct alerts (each gets a fresh UUID and timestamp) instead of piling up identical hardcoded test rows.

---

## 4. Risks and Trade-offs (Summary)

**No read/query interface:** this table only supports writes today — checking `OPEN` alerts or updating `status` to `RESOLVED` would need a separate script or a small CLI extension, not implemented here.

**Wired into other automation:** `ec2-open-ports`, `s3_security_scanner`, and `ec2-auto-remediation` in this portfolio all write to this table now — each with its own local `log_alert()` matching this signature, since these are independent scripts (one is a Lambda deployment package) rather than a shared installable package. A real shared library would need proper packaging; duplicating this small function across four call sites is the practical trade-off for a lab-scale portfolio, not an oversight.

**No deduplication:** logging the same finding twice creates two separate items — there's no check for "is this alert already open" before writing.

---

## How to Run

```bash
pip install -r requirements.txt
aws configure
python main.py --severity HIGH --message "Your finding here"
```

## Tech Stack

* **Language:** Python 3
* **SDK:** AWS Boto3
* **Storage:** Amazon DynamoDB (`PAY_PER_REQUEST`, PITR enabled)
