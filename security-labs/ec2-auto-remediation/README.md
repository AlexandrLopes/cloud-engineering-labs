# AWS Security Auto-Remediation Bot (SOAR)

**Serverless bot that detects and auto-reverts risky Security Group changes in near real-time — no human in the loop, with every trade-off made explicit.**

## 1. Context and Objective

A misconfigured Security Group opening SSH (22) or RDP (3389) to `0.0.0.0/0` is one of the most common causes of brute-force compromise, and the exposure window matters more than most controls admit — a rule open for even a few minutes is enough for automated scanners to find it.

This bot closes that window automatically: **event-driven detection** (CloudTrail → EventBridge → Lambda) that revokes non-compliant rules sub-second from creation, instead of waiting for a periodic compliance scan.

**Out of scope:** notification/alerting on remediation events (currently CloudWatch Logs only, no SNS), multi-account deployment, ports beyond 22/3389.

---

## 2. Architecture

```
User/Attacker creates a risky SG rule
  -> AWS CloudTrail captures the API call
  -> Amazon EventBridge matches the pattern (AuthorizeSecurityGroupIngress)
  -> AWS Lambda triggered
  -> Python logic validates compliance (0.0.0.0/0 on port 22/3389)
  -> Non-compliant? Lambda revokes the rule immediately via API
  -> Action logged to CloudWatch
```

Event-driven, not polling-based — this is what gets the response time to sub-second instead of a periodic scan interval (AWS Config's managed rules, by comparison, typically evaluate on a schedule or on resource change with added propagation delay).

---

## 3. Detection and Remediation Path: Custom Lambda, Not AWS Config

**Decision: EventBridge + Lambda, not AWS Config Rules with auto-remediation.**

AWS Config has a managed path for exactly this (`restricted-ssh` managed rule + a remediation action). It was **not** used here because [VALIDATE: fill in your actual reason — e.g. "Config has to be enabled and configured per-region/account as a prerequisite service, and this project's goal was to show the underlying event-driven mechanism (CloudTrail → EventBridge → Lambda) rather than depend on a managed compliance layer" — or your real reason if different].

**Trade-off accepted:** a custom Lambda means this logic isn't automatically visible in AWS Config's compliance dashboard, and any port/condition beyond 22 and 3389 requires a code change instead of a rule parameter. In an account already standardized on AWS Config, the managed rule would likely be the lower-maintenance choice.

---

## 4. Remediation Behavior: No Grace Window

**Decision: revoke immediately, no confirmation, no delay.**

The bot does not check whether the change was intentional (e.g. a break-glass rule opened briefly for emergency debugging) — any rule matching `0.0.0.0/0` on port 22 or 3389 is reverted the moment it's detected.

**Trade-off accepted:** this favors security posture over operational convenience. A legitimate emergency access rule gets revoked just like a mistaken one — the mitigation for that scenario is the **CIDR allowlist** (corporate VPN ranges pass through untouched), not a manual override. If break-glass SSH access were a real operational need beyond the allowlisted ranges, this would need an explicit exception path (e.g. a tagged "temporary-allow" rule with a TTL) — not implemented here.

---

## 5. Scope: Ports 22 and 3389 Only

**Decision: hardcoded to SSH and RDP, not a generic port-exposure scanner.**

These two ports were targeted specifically because they're the highest-signal indicators of brute-force risk — direct remote shell access exposed to the internet. [VALIDATE: if you also considered other ports like 3306/5432 and deliberately excluded them, state why here — e.g. "database ports are typically already inside private subnets in this project's other stacks, so the marginal risk is lower" — or correct this if the real reason is different, e.g. simply out of scope for a first version.]

**Trade-off accepted:** a database port or another sensitive service opened to `0.0.0.0/0` would **not** be caught by this bot today. Extending the port list is a one-line change in the Lambda's compliance check, but it isn't automatic.

---

## 6. Permissions Model

**Decision: single-permission IAM role.**

The Lambda's execution role is scoped to exactly one EC2 action — `ec2:RevokeSecurityGroupIngress` — plus CloudWatch Logs write. It cannot terminate instances, read S3, modify IAM, or touch any resource outside that one action.

**Why this matters under scrutiny:** an auto-remediation bot is, by definition, a piece of automation with write access triggered by an event it doesn't fully control. If the Lambda itself were ever compromised or had a logic bug, the blast radius is capped at "can revoke SG ingress rules" — nothing else.

---

## 7. Legitimate Access: CIDR Allowlisting

Corporate VPN ranges and other known-legitimate CIDRs are explicitly allowlisted in the compliance check, so the bot doesn't fight real operational access. This is the primary safeguard against the "no grace window" trade-off in section 4 — legitimate traffic never triggers remediation in the first place, rather than being remediated and needing a manual revert.

**Maintenance cost:** the allowlist is static and needs to be updated manually if the corporate IP range changes. No automated sync with, e.g., a VPN provider's published ranges.

---

## 8. Risks and Trade-offs (Summary)

**Custom Lambda vs AWS Config managed rule:** full control over the exact CloudTrail→EventBridge→Lambda mechanism, at the cost of not integrating with Config's compliance dashboard and needing code changes to extend scope.

**No grace window:** legitimate emergency rules are revoked like any other violation; the CIDR allowlist is the only safety valve.

**Fixed port scope (22/3389):** highest-signal ports covered; other sensitive ports (e.g. database ports) are not monitored by this bot.

**Static CIDR allowlist:** no automatic sync with external IP range sources; stale entries are a manual maintenance item.

**No alerting beyond CloudWatch Logs:** remediation actions are logged but nobody gets paged — this is an audit trail, not an incident notification system today.

---

## 9. How to Test

```bash
terraform init
terraform apply
```

1. **Simulate an attack:**
   - AWS Console → **EC2** → **Security Groups**.
   - Select (or create) a test Security Group.
   - **Edit inbound rules** → **Add rule**: Type **SSH** (Port 22), Source **Anywhere-IPv4** (`0.0.0.0/0`).
   - **Save rules**.
2. **Verify remediation:**
   - Wait 5–10 seconds, refresh the Security Group page.
   - **Result:** the rule disappears automatically.
3. **Check logs:**
   - **CloudWatch Logs** → `/aws/lambda/security-group-auto-remediation`.
   - Look for: `SUCCESS: Insecure rule revoked automatically.`

---

## Tech Stack

* **Infrastructure as Code:** Terraform
* **Compute:** AWS Lambda (Python 3.9)
* **SDK:** Boto3 (AWS SDK for Python)
* **Orchestration:** Amazon EventBridge (CloudWatch Events)
* **Permissions:** AWS IAM (Least Privilege: `ec2:RevokeSecurityGroupIngress`)
