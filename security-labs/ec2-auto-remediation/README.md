# AWS Security Auto-Remediation Bot (SOAR)

**Serverless bot that detects and auto-reverts risky Security Group changes in near real-time — no human in the loop, with every trade-off made explicit.**

## 1. Context and Objective

A misconfigured Security Group opening SSH (22) or RDP (3389) to `0.0.0.0/0` is one of the most common causes of brute-force compromise, and the exposure window matters more than most controls admit — a rule open for even a few minutes is enough for automated scanners to find it.

This bot closes that window automatically: **event-driven detection** (CloudTrail → EventBridge → Lambda) that revokes non-compliant rules sub-second from creation, instead of waiting for a periodic compliance scan.

**Out of scope:** notification/alerting on remediation events (currently CloudWatch Logs only, no SNS), multi-account deployment, ports beyond 22/3389.

**A note on this README's own history:** an earlier version of this document described a CIDR allowlist and IPv6/all-traffic detection as if they already existed. They didn't — the code only checked IPv4 ranges on exactly ports 22/3389, with zero exception mechanism for legitimate traffic. This version documents what's actually implemented now, after closing those gaps (Sections 4, 5, and 7).

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

AWS Config has a managed path for exactly this (`restricted-ssh` managed rule + a remediation action). This project builds the mechanism directly instead — CloudTrail, EventBridge, and Lambda wired by hand — to demonstrate the underlying event-driven pattern rather than rely on a managed compliance layer that hides it. Config also has to be explicitly enabled per-region/account as a prerequisite service; this Lambda has no such dependency.

**Trade-off accepted:** a custom Lambda means this logic isn't automatically visible in AWS Config's compliance dashboard, and any port/condition beyond 22 and 3389 requires a code change instead of a rule parameter. In an account already standardized on AWS Config, the managed rule would likely be the lower-maintenance choice.

---

## 4. Remediation Behavior: No Grace Window

**Decision: revoke immediately, no confirmation, no delay.**

The bot does not check whether the change was intentional (e.g. a break-glass rule opened briefly for emergency debugging) — any public rule on a risky port is reverted the moment it's detected, unless its CIDR falls inside the allowlist (Section 7).

**Trade-off accepted:** this favors security posture over operational convenience. A legitimate emergency access rule from an unlisted range gets revoked just like a mistaken one — the only safety valve is the allowlist itself. If break-glass SSH access were a real operational need beyond what's allowlisted, this would need an explicit exception path (e.g. a tagged "temporary-allow" rule with a TTL) — not implemented here.

---

## 5. Scope: Ports 22 and 3389 Only

**Decision: hardcoded to SSH and RDP, not a generic port-exposure scanner.**

These two ports were targeted specifically because they're the highest-signal indicators of brute-force risk — direct remote shell access exposed to the internet. Out of scope for this version, not evaluated and excluded — extending to other sensitive ports (e.g. 3306, 5432) is a real next step, not a decision that was made and rejected.

**The gap this closes: all-traffic rules and IPv6 were invisible.** The earlier version only checked `ipRanges` (IPv4) and only matched when `fromPort`/`toPort` exactly equaled 22 or 3389 — a rule with `IpProtocol: "-1"` (all ports, all protocols) has no `fromPort`/`toPort` at all, so the widest possible exposure passed through unflagged, the same class of bug found and fixed in `ec2-open-ports` in this same portfolio. IPv6 (`ipv6Ranges`, `::/0`) was never checked either. Both are fixed now: a missing `fromPort`/`toPort` is always treated as maximally risky, and IPv6 ranges are evaluated in parallel with IPv4.

**Trade-off accepted:** a database port or another sensitive service opened to `0.0.0.0/0` on a *specific* port (not all-traffic) would still **not** be caught by this bot today. Extending the port list is a one-line change in `RISKY_PORTS`.

---

## 6. Permissions Model

**Decision: single-permission IAM role, on the EC2 side.**

**The gap this closes:** an earlier version of this README claimed the role was scoped to exactly one EC2 action — it wasn't. The actual policy also granted `ec2:DescribeSecurityGroups`, which `remediation.py` never calls anywhere (the Lambda reads everything it needs directly from the CloudTrail event payload, never queries the API for SG state). An unused permission is still something an attacker gets if the role is ever compromised.

**Fixed:** `ec2:DescribeSecurityGroups` removed. The role is now genuinely scoped to exactly one EC2 action — `ec2:RevokeSecurityGroupIngress` — plus CloudWatch Logs write. It cannot terminate instances, read S3, modify IAM, or touch any resource outside that one action.

**Why this matters under scrutiny:** an auto-remediation bot is, by definition, a piece of automation with write access triggered by an event it doesn't fully control. If the Lambda itself were ever compromised or had a logic bug, the blast radius is capped at "can revoke SG ingress rules" — nothing else.

---

## 7. Legitimate Access: CIDR Allowlisting

**The gap this closes:** this section, in an earlier version of this README, described a corporate-VPN allowlist as an already-implemented safeguard. It wasn't — there was no exception mechanism in the code at all. Every public rule on a risky port was revoked unconditionally, including legitimate emergency access.

**Fixed:** `ALLOWED_CIDR_RANGES` (a Lambda environment variable, wired from a new Terraform variable `allowed_cidr_ranges`) holds a comma-separated list of known-legitimate CIDRs — e.g. a corporate VPN range. `remediation.py` checks whether the newly-opened CIDR is contained within (or equal to) any allowlisted range using Python's `ipaddress` module, not a naive string match, so a `/32` inside a broader allowlisted `/24` is correctly recognized as covered. Empty by default — nothing is exempted unless explicitly configured.

**Maintenance cost:** the allowlist is static and needs to be updated manually if the corporate IP range changes. No automated sync with, e.g., a VPN provider's published ranges.

---

## 8. Risks and Trade-offs (Summary)

**Custom Lambda vs AWS Config managed rule:** full control over the exact CloudTrail→EventBridge→Lambda mechanism, at the cost of not integrating with Config's compliance dashboard and needing code changes to extend scope.

**CIDR allowlist (fixed):** was fabricated documentation with no implementation; now a real, tested mechanism via `ALLOWED_CIDR_RANGES`. Still the only safety valve — no grace window or manual-override path beyond it.

**All-traffic and IPv6 detection (fixed):** an all-ports rule (`IpProtocol: "-1"`) and IPv6 public exposure were both invisible before; both are caught now, matching the fix applied to `ec2-open-ports`.

**Overpermissive IAM role (fixed):** `ec2:DescribeSecurityGroups` was granted but never used; removed.

**Fixed port scope (22/3389):** highest-signal ports covered; other sensitive ports (e.g. database ports) are not monitored by this bot — out of scope, not evaluated and rejected.

**Static CIDR allowlist:** no automatic sync with external IP range sources; stale entries are a manual maintenance item.

**No alerting beyond CloudWatch Logs:** remediation actions are logged but nobody gets paged — this is an audit trail, not an incident notification system today.

---

## 9. How to Test

```bash
# Optional: set your own known-legitimate ranges, comma-separated
echo 'allowed_cidr_ranges = "203.0.113.0/24"' > terraform.tfvars

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
* **Permissions:** AWS IAM (Least Privilege: `ec2:RevokeSecurityGroupIngress` + CloudWatch Logs write, nothing else)
