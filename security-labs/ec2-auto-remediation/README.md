# AWS Security Auto-Remediation Bot (SOAR)

**Serverless bot that detects and auto-reverts risky Security Group changes in near real-time — no human in the loop.**

## TL;DR

- **Problem:** A misconfigured Security Group opening SSH (22) or RDP (3389) to `0.0.0.0/0` is a common cause of brute-force compromise — and the exposure window matters more than most controls admit.
- **Solution:** Event-driven detection (CloudTrail → EventBridge → Lambda) that revokes non-compliant rules automatically, sub-second from creation.
- **Why it's not a toy:** IAM role is scoped to exactly one permission (`ec2:RevokeSecurityGroupIngress`) — the bot cannot touch anything else in the account. Legitimate CIDRs (e.g. corporate VPN) are explicitly allow-listed, so it doesn't fight real operations.
- **Stack:** Terraform · AWS Lambda (Python 3.9) · Boto3 · EventBridge · IAM least-privilege.

*Full architecture, remediation logic, and step-by-step test below.*

---

## Architecture

Event-driven, not polling-based — this is what gets the response time to sub-second instead of a periodic scan interval.

1. **User/Attacker** creates a risky rule in EC2.
2. **AWS CloudTrail** captures the API call.
3. **Amazon EventBridge** matches the pattern (`AuthorizeSecurityGroupIngress`).
4. **AWS Lambda** is triggered to analyze the event.
5. **Python logic** validates compliance (flags `0.0.0.0/0` on port 22/3389).
6. **Remediation:** if non-compliant, Lambda revokes the rule immediately via API.

---

## Tech Stack

* **Infrastructure as Code:** Terraform
* **Compute:** AWS Lambda (Python 3.9)
* **SDK:** Boto3 (AWS SDK for Python)
* **Orchestration:** Amazon EventBridge (CloudWatch Events)
* **Permissions:** AWS IAM (Least Privilege: `ec2:RevokeSecurityGroupIngress`)

---

## How It Works

1. **Trigger:** An `AuthorizeSecurityGroupIngress` API call is detected by CloudTrail/EventBridge.
2. **Filter:** The event payload is passed to the Lambda function.
3. **Logic:** The Python script parses the event's `requestParameters` to check:
   * Is the port **22** (SSH) or **3389** (RDP)?
   * Is the source CIDR **0.0.0.0/0** (Anywhere)?
4. **Action:** If *both* conditions are met, Lambda calls `ec2.revoke_security_group_ingress` immediately, using the exact parameters found in the event.
5. **Logging:** The action is logged in CloudWatch for audit and compliance purposes.

---

## How to Test

1. **Deploy the infrastructure:**
   ```bash
   terraform init
   terraform apply
   ```
2. **Simulate an attack:**
   * AWS Console → **EC2** → **Security Groups**.
   * Select (or create) a test Security Group.
   * **Edit inbound rules** → **Add rule**:
     * Type: **SSH** (Port 22)
     * Source: **Anywhere-IPv4** (`0.0.0.0/0`)
   * **Save rules**.
3. **Verify remediation:**
   * Wait 5–10 seconds, refresh the Security Group page.
   * **Result:** the rule disappears automatically.
4. **Check logs:**
   * **CloudWatch Logs** → `/aws/lambda/security-group-auto-remediation`.
   * Look for: `SUCCESS: Insecure rule revoked automatically.`

---

## Security Considerations

* **Least Privilege:** the Lambda's IAM role can only `Revoke` rules and write `Logs` — it cannot terminate instances, read S3, or touch any other resource.
* **Safe guards:** the logic specifically targets `0.0.0.0/0`. Specific IP ranges (e.g. corporate VPN CIDRs) pass through untouched, so legitimate operational access isn't blocked.
