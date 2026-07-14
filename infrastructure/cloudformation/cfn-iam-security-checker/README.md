# Serverless IAM Security Checker (CloudFormation Native)

**Daily, automated compliance audit for IAM MFA coverage — event-driven, least-privilege, with every trade-off made explicit.**

## 1. Context and Objective

An IAM user without MFA is a standing risk that's easy to lose track of as an account grows — new users get created, MFA enrollment gets skipped, and nobody notices until it's relevant in an incident or an audit. This runs a daily automated check instead of relying on someone remembering to look.

```
EventBridge (daily cron, 08:00 UTC) -> Lambda -> iam:ListUsers / iam:ListMFADevices -> SNS (email alert if non-compliant)
```

---

## 2. Detection Logic

The Lambda lists every IAM user in the account, then checks each one for at least one registered MFA device. Any user with zero MFA devices goes into a list; if that list is non-empty, a single SNS email is sent naming every non-compliant user and referencing CIS Benchmark alignment.

**Trade-off accepted:** this is a binary check (has MFA / doesn't), not a check of MFA *type* — a user with only a less-robust MFA method (SMS, where supported) would still pass. Extending this to check device type would need `iam:ListMFADevices`' response parsed further.

---

## 3. Schedule: Daily Cron, Not Real-Time

**Decision: EventBridge scheduled rule (`cron(0 8 * * ? *)`), not event-driven on user creation.**

Unlike `ec2-auto-remediation` (this repo's other security automation, which reacts to a Security Group change in near real-time via CloudTrail/EventBridge), MFA compliance doesn't need sub-second detection — a user created without MFA is a slow-burn risk, not an active exposure like an open SSH port. A daily check catches it within 24 hours, which is an acceptable window for this specific risk.

**Trade-off accepted:** a user without MFA is exposed for up to 24 hours before the daily check catches it. Real-time detection would require listening for `iam:CreateUser` via CloudTrail/EventBridge instead — deliberately not the design here, since the risk profile doesn't demand it the way an open ingress port does.

---

## 4. Permissions Model

The Lambda's execution role is scoped to exactly three actions: `iam:ListUsers`, `iam:ListMFADevices` (both require `Resource: "*"` — this is an AWS requirement for these specific list-style IAM actions, not a permissions shortcut), and `sns:Publish` restricted to the one SNS topic this stack creates. It cannot modify any IAM user, revoke access, or touch any resource outside its own alert topic.

---

## 5. Operational Note: Email Subscriptions Require Manual Confirmation

The `AWS::SNS::Subscription` resource with `Protocol: email` sends a confirmation link to the provided address — **the subscription is pending, not active, until that link is clicked.** Deploying this stack alone does not guarantee alerts arrive; the `AlertEmail` recipient needs to confirm the subscription once after the first deploy. Worth checking after `create-stack` completes, not assuming it "just works."

---

## 6. Risks and Trade-offs (Summary)

**Daily cron vs event-driven:** appropriate response time for a slow-burn risk (missing MFA); up to a 24-hour detection window, deliberately accepted.

**Binary MFA check:** doesn't distinguish MFA strength/type — any registered device counts.

**Single email alert, no dashboard:** compliance state is only visible via the alert email when there's a violation; there's no persistent compliance dashboard (e.g. writing results to DynamoDB or S3 for historical tracking) — a user could be compliant one day, non-compliant the next, non-compliant again, and each state only surfaces as a point-in-time email, not a trend.

**Subscription confirmation is a manual step:** easy to deploy and assume it's working when the email link was never clicked.

---

## How to Deploy

```bash
aws cloudformation create-stack \
  --stack-name iam-security-audit-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=AlertEmail,ParameterValue=your.email@example.com \
  --capabilities CAPABILITY_IAM
```

After the stack completes, check the provided email for the SNS subscription confirmation link — the alert won't be delivered until it's clicked.

## Tech Stack

* **Infrastructure as Code:** AWS CloudFormation
* **Scheduling:** Amazon EventBridge (cron)
* **Compute:** AWS Lambda (Python 3.12)
* **Alerting:** Amazon SNS
* **Permissions:** AWS IAM (least privilege)
