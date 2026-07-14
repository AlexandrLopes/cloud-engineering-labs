# AWS Security Group Auditor

**Python automation that scans EC2 Security Groups for internet-exposed risky ports — including the exposure patterns a naive port-list check misses.**

## 1. Context and Objective

Leaving sensitive ports (SSH 22, RDP 3389) open to `0.0.0.0/0` is one of the most common causes of compromise in cloud environments, and manual auditing across many Security Groups doesn't scale. This script automates the check: fetch every Security Group, inspect inbound rules, flag public exposure on risky ports.

---

## 2. The Gap This Closes: "All Traffic" Rules Were Invisible

**What the earlier version actually did:** it only inspected rules where a `FromPort` key was present. In the AWS API, a rule with `IpProtocol: "-1"` — meaning **all ports, all protocols** — has no `FromPort`/`ToPort` at all. That's not an edge case to skip; it's the single worst possible Security Group misconfiguration (the entire host open to the internet), and the original check filtered it out before ever looking at the CIDR.

**Fixed:** the port check now treats a missing `FromPort`/`ToPort` as "all ports," which is always flagged as risky regardless of the `RISKY_PORTS` list — an all-traffic rule open to the internet is never a false negative now.

---

## 3. The Second Gap: IPv4 Only

**What the earlier version actually did:** checked `IpRanges` (IPv4) exclusively. A rule allowing SSH from `::/0` (IPv6 "anywhere") passed through unexamined — same exposure, different address family, invisible to the audit.

**Fixed:** `Ipv6Ranges` is now checked in parallel with `IpRanges`, using the same risky-port logic for both.

---

## 4. Detection Logic

For every inbound rule on every Security Group:
1. Determine if the rule is scoped to specific ports or is an all-traffic rule (`IpProtocol == "-1"`).
2. Check both `IpRanges` (IPv4, `0.0.0.0/0`) and `Ipv6Ranges` (IPv6, `::/0`) for public exposure.
3. If exposed to the internet **and** (all-traffic rule **or** overlaps `RISKY_PORTS = [22, 3389, 8080]`), flag it — all-traffic rules are always flagged regardless of the port list, since by definition they include every risky port.

---

## 5. Risks and Trade-offs (Summary)

**Configurable risky-port list, not a full exposure audit:** `RISKY_PORTS` covers SSH, RDP, and 8080 — a port not on that list (e.g. a database port like 3306 opened by mistake) still passes unless it's part of an all-traffic rule. Extending coverage means extending the list, not a structural change.

**No egress (outbound) analysis:** this audits inbound rules only — an overly permissive outbound rule isn't in scope.

**Read-only, no remediation:** unlike `ec2-auto-remediation` in this same portfolio (which detects and auto-reverts risky rules in near real-time via EventBridge), this is a point-in-time audit script — it reports, it doesn't act. Running it is a manual or scheduled step, not an always-on control.

---

## How to Run

```bash
pip install boto3
python main.py
```

## Tech Stack

* **Language:** Python 3
* **SDK:** AWS Boto3 (`describe_security_groups`)
