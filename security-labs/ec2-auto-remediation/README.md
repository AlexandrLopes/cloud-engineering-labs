#  AWS Security Auto-Remediation Bot (SOAR)

**Automated Incident Response for Security Group Misconfigurations.**

##  Overview
In Cloud Security, **exposure time** is critical. A Security Group rule opening port 22 (SSH) or 3389 (RDP) to the entire internet (`0.0.0.0/0`) can lead to a brute-force compromise in minutes.

This project implements a **Serverless SOAR (Security Orchestration, Automation, and Response)** solution. It acts as an autonomous "security guard" that actively listens for risky network changes and instantly reverts them, enforcing a **Zero Trust** posture.

---

##  Architecture

The solution uses an **Event-Driven Architecture** to ensure near real-time remediation (sub-second response).

1.  **User/Attacker** creates a risky rule in EC2.
2.  **AWS CloudTrail** captures the API call.
3.  **Amazon EventBridge** detects the specific pattern (`AuthorizeSecurityGroupIngress`).
4.  **AWS Lambda** is triggered to analyze the event.
5.  **Python Logic** validates if the rule is compliant (detects `0.0.0.0/0` on port 22/3389).
6.  **Remediation:** If non-compliant, Lambda immediately revokes the rule via API.

---

##  Tech Stack

* **Infrastructure as Code:** Terraform
* **Compute:** AWS Lambda (Python 3.9)
* **SDK:** Boto3 (AWS SDK for Python)
* **Orchestration:** Amazon EventBridge (CloudWatch Events)
* **Permissions:** AWS IAM (Least Privilege: `ec2:RevokeSecurityGroupIngress`)

---

##  How It Works

The automation follows this strict logical flow:

1.  **Trigger:** An `AuthorizeSecurityGroupIngress` API call is detected by CloudTrail/EventBridge.
2.  **Filter:** The event payload is passed to the Lambda function.
3.  **Logic:** The Python script parses the event `requestParameters` to check:
    * Is the port **22** (SSH) or **3389** (RDP)?
    * Is the source CIDR **0.0.0.0/0** (Anywhere)?
4.  **Action:** If *both* conditions are met, the Lambda calls `ec2.revoke_security_group_ingress` immediately using the exact parameters found in the event.
5.  **Logging:** The action is logged in CloudWatch for audit and compliance purposes.

---

##  Project Structure

```text
.
├── main.tf           # Terraform configuration (Lambda, EventBridge Rule, IAM Roles)
├── remediation.py    # Python logic for event parsing and remediation
└── README.md         # Documentation
```

## How to Test

1.  **Deploy the infrastructure:**
    ```bash
    terraform init
    terraform apply
    ```

2.  **Simulate an Attack:**
    * Go to the AWS Console -> **EC2** -> **Security Groups**.
    * Select any Security Group (or create a test one).
    * Click **Edit inbound rules** -> **Add rule**.
        * Type: **SSH** (Port 22)
        * Source: **Anywhere-IPv4** (0.0.0.0/0)
    * Click **Save rules**.

3.  **Verify Remediation:**
    * Wait 5-10 seconds.
    * Refresh the Security Group page (Browser Refresh).
    * **Result:** The rule will disappear automatically.

4.  **Check Logs:**
    * Go to **CloudWatch Logs** -> `/aws/lambda/security-group-auto-remediation`.
    * Look for the log entry: `SUCCESS: Insecure rule revoked automatically.`

---

## Security Considerations

* **Least Privilege:** The Lambda function IAM Role is strictly scoped. It can only `Revoke` rules and write `Logs`. It cannot delete EC2 instances, read S3 buckets, or modify other resources.
* **Safe Guards:** The logic specifically targets `0.0.0.0/0`. It allows specific IP ranges (e.g., Corporate VPN CIDRs) to pass through, ensuring legitimate operational access is not blocked.