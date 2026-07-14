# Serverless High-Volume eSIM Order Processor

**Event-driven, serverless architecture for processing high-volume eSIM activation orders asynchronously — decoupled from ingestion, with every trade-off made explicit.**

## 1. Context and Objective

eSIM activation orders arrive in unpredictable bursts (e.g. a promotional campaign or Black Friday spike). Processing them synchronously against a database couples ingestion throughput directly to database throughput — if the DB throttles, requests fail or queue up in front of the customer.

This project decouples the two: an SQS queue absorbs the burst, Lambda drains it at a sustainable rate, and DynamoDB stores the result. The queue is the shock absorber.

**Scope note:** the eSIM profile generation step (ICCID assignment) is **simulated** in this project — it produces a well-formed record with the right shape and constraints (uniqueness, format), but does not implement the real cryptographic provisioning protocol (SM-DP+ / GSMA RSP) that a production eSIM platform would use. The architecture around it — queueing, batching, idempotency, storage — is real and is what this project is demonstrating.

---

## 2. Architecture (Decoupled Flow)

```
Client -> Amazon SQS (ingestion buffer)
       -> AWS Lambda (batch processor, triggered by SQS)
       -> Amazon DynamoDB (active eSIM profile storage)
```

1. **Amazon SQS (ingestion):** receives incoming eSIM activation requests concurrently, buffering bursts instead of passing them straight to the database.
2. **AWS Lambda (processing):** triggered automatically by SQS, pulls messages in batches, generates the eSIM profile record (ICCID — simulated, see Section 1), and writes to storage.
3. **Amazon DynamoDB (storage):** stores the successfully generated active eSIM profiles.

---

## 3. Storage Layer: DynamoDB, Not RDS

**Decision: DynamoDB for the active eSIM profile store.**

The table (`esim-active-profiles`) uses a single hash key (`order_id`), `PAY_PER_REQUEST` billing, and no secondary indexes — the access pattern is a pure key lookup, not relational querying across tables, which is exactly what DynamoDB is built for. `PAY_PER_REQUEST` also means no capacity planning ahead of a traffic spike, which matters directly for the "Black Friday burst" scenario this project targets.

Contrast with `aws-3tier-infrastructure`, where the data is genuinely relational (a users table expected to grow foreign-key-style relationships) — DynamoDB there would fight the access pattern instead of fitting it.

**Trade-off accepted:** no ad-hoc relational queries (e.g. "all orders from customer X joined with billing") without a secondary index or a separate analytics path — not needed for this project's single-key access pattern, but a real constraint if requirements grew.

---

## 4. Ingestion Buffer: SQS, Not Kinesis

**Decision: standard SQS queue for ingestion, not Kinesis Data Streams.**

Each order is processed independently, with no need for ordered replay across multiple consumers — SQS's simpler "buffer, process once, delete" model fits a single-consumer pipeline without Kinesis's stream/shard overhead.

**Security detail worth noting:** the queue is encrypted with a **customer-managed KMS key** (rotation enabled), not the SQS default key — the template comment marks this as a direct fix for a Trivy finding (`AWS-0135`), i.e. this project went through an actual security scan and the encryption choice is a documented response to it, not a default.

**Trade-off accepted:** no built-in replay (once a message is deleted, it's gone — unlike Kinesis's retention window), and no fan-out to multiple independent consumers without additional plumbing (SNS+SQS fan-out pattern).

---

## 5. Processing: Lambda Batching, With Partial Failure Reporting

Lambda is configured to pull batches of up to 10 messages from SQS per invocation (`BatchSize: 10`), not one message per invocation — amortizing cold/warm start overhead across multiple orders per invocation, which is what actually delivers the "high-volume" part of the design.

The event source mapping enables `ReportBatchItemFailures`, and the handler returns the specific `messageId`s that failed instead of a blanket success. This means SQS retries **only the orders that actually failed**, not the entire batch — a batch of 10 where 1 write fails doesn't force 9 successful orders to be reprocessed.

---

## 6. Resilience: Dead-Letter Queue and Alerting

**The gap this closes:** the first version of this Lambda caught per-record exceptions, logged them, and moved on — but always returned success for the invocation. Under the SQS-Lambda integration, that meant every message in the batch was deleted from the queue regardless of whether the individual `put_item` call actually succeeded. A DynamoDB throttle or write error meant a silently lost order: no retry, no record anywhere except a CloudWatch log line easy to miss.

**Fixed with three changes:**

1. **`ReportBatchItemFailures` enabled** on the event source mapping (Section 5) — only genuinely failed messages are returned to the queue instead of being deleted alongside successful ones.
2. **A dead-letter queue** (`esim-orders-dlq`) is attached via `RedrivePolicy` with `maxReceiveCount: 3` — a message that fails 3 delivery attempts moves to the DLQ instead of retrying forever or being silently dropped. 14-day retention on the DLQ gives enough time to investigate before it expires.
3. **A CloudWatch alarm** on the DLQ's `ApproximateNumberOfMessagesVisible` fires the moment a single message lands there, publishing to an SNS topic (`esim-dlq-alerts`) — so a failed order surfaces as an actual notification, not something someone has to go looking for in logs.

**What's still not automated:** re-driving messages from the DLQ back into the main queue after the root cause is fixed is a manual operation today (`aws sqs` CLI or a redrive task in the console) — no automated reprocessing pipeline. Acceptable for the current scale; would be the next thing to build if failure volume grew.

---

## 7. Infrastructure as Code: CloudFormation, Not Terraform

Unlike the other Terraform-based projects in this portfolio, this one is provisioned with **AWS CloudFormation** — a deliberate choice to demonstrate comfort with AWS's native IaC tool, not just the third-party standard. IAM least-privilege roles are provisioned as part of the same template, scoped to exactly what the Lambda needs (SQS read/delete, DynamoDB write).

---

## 8. Risks and Trade-offs (Summary)

**DynamoDB vs RDS:** fits the single-key access pattern (`order_id` hash key, `PAY_PER_REQUEST`) and scales under bursty writes without capacity planning ahead of time; loses relational query flexibility.

**SQS vs Kinesis:** simpler model for a single-consumer, non-replay pipeline; no replay window or native fan-out. Queue is encrypted with a customer-managed KMS key, a direct response to a Trivy security finding.

**Batch processing + partial failure reporting:** amortizes Lambda invocation overhead at scale (`BatchSize: 10`) while isolating retries to only the messages that actually failed, not the whole batch.

**DLQ + alerting:** a message that fails 3 attempts moves to a dead-letter queue instead of disappearing, and a CloudWatch alarm surfaces it via SNS. Redriving from the DLQ back to the main queue after a fix is still a manual step — no automated reprocessing pipeline yet.

**Simulated eSIM generation:** the architecture (queueing, decoupling, storage) is real and load-bearing; the cryptographic provisioning step is not implemented and is explicitly out of scope, not hidden.

---

## Tech Stack

* **Infrastructure as Code:** AWS CloudFormation
* **Ingestion:** Amazon SQS (SSE-KMS, customer-managed key)
* **Compute:** AWS Lambda (Python 3.12)
* **Storage:** Amazon DynamoDB (`PAY_PER_REQUEST`)
* **Permissions:** AWS IAM (Least Privilege, scoped per-action)
