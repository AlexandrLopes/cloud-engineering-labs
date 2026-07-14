# AWS IAM User Auditor

**Python automation auditing three independent IAM risk signals per user — MFA status, login inactivity, and access key age — with every gap between claim and code closed.**

## 1. Context and Objective

Stale credentials are one of the quietest risks in an AWS account: a user who stopped logging in, an access key nobody rotated, MFA that was never enabled. None of these show up unless someone specifically checks — this script checks all three, per user, in one pass.

---

## 2. The Gap This Closes: Login Inactivity Was Never Actually Checked

**What the earlier version actually did:** the tool was named and described as an inactive-user auditor — flagging accounts with no login in 90+ days, based on `PasswordLastUsed`. The code never read that field. What it actually computed was MFA status and **access key age**, unrelated signals to login recency. The README described one tool; the code was a different one.

**Fixed:** `PasswordLastUsed` is now read directly from `list_users()` and compared against `INACTIVITY_THRESHOLD_DAYS` (90, configurable). A user with no `PasswordLastUsed` is reported as "No console login" rather than assumed inactive — that field is absent both for users who never logged in via console **and** for API/CLI-only users with no console access at all, and the API response doesn't distinguish the two. Flagging that distinction explicitly instead of guessing is more defensible than a false "inactive" label on a legitimate service account.

---

## 3. Three Independent Checks, Not One Score

Each user gets evaluated on three axes that don't reduce to a single number:
1. **MFA:** enabled or disabled — binary.
2. **Login inactivity:** days since `PasswordLastUsed`, or "no console login" if never set.
3. **Access key age:** per key, `CRITICAL` if active and >90 days old, `WARNING` if active and >60 days old, `OK` otherwise.

A user can be flagged on any combination of the three — an active console user with a stale unrotated key is a different risk than a dormant account with MFA disabled, and collapsing both into one "risk score" would hide which specific control is missing.

---

## 4. Risks and Trade-offs (Summary)

**No console access vs never logged in — same signal, different meaning:** the script can't distinguish these from `PasswordLastUsed` alone; both need a human to check whether the user is meant to have console access at all.

**Key age vs key usage:** the tool flags keys by *creation* age, not by *last actual use* (`GetAccessKeyLastUsed` is a separate API call, not used here) — a key created 100 days ago but used yesterday still gets flagged the same as one that's been dormant the whole time. Adding last-used data would sharpen this but requires one additional API call per key.

**No automated remediation:** this reports; it doesn't deactivate keys, disable users, or enforce MFA. Pairing this with `ec2-auto-remediation`'s pattern (detect → act automatically) would be the natural next step if this needed to be more than an audit tool.

---

## How to Run

```bash
pip install boto3
aws configure
python main.py
```

## Tech Stack

* **Language:** Python 3
* **SDK:** AWS Boto3
* **APIs used:** `iam:ListUsers`, `iam:ListMFADevices`, `iam:ListAccessKeys`
