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

## 5. Processing: Lambda Batching, Not One-Invocation-Per-Message

Lambda is configured to pull batches of up to 10 messages from SQS per invocation (`BatchSize: 10`), not one message per invocation — amortizing cold/warm start overhead across multiple orders per invocation, which is what actually delivers the "high-volume" part of the design.

**Known gap: no partial batch failure reporting.** `ReportBatchItemFailures` is **not** enabled on the event source mapping. This has a direct consequence, covered in the next section.

---

## 6. Known Gap: Silent Order Loss on Processing Failure

This is the most important trade-off in the project, and it's a real limitation, not a hypothetical one.

**What happens today:** the Lambda handler wraps each record's processing in a `try/except` that **catches and logs** any error (e.g. a DynamoDB write failure) but does not re-raise it. The function always returns success for the invocation. Under the SQS-Lambda integration, that means **every message in the batch is deleted from the queue**, regardless of whether an individual record's `put_item` actually succeeded.

**Concrete failure mode:** if DynamoDB throttles or rejects a single write, that order's exception is printed to CloudWatch Logs and the loop moves on — the order is **not stored**, and the message is **still removed from the queue**, so there is no retry and no dead-letter capture. There is also no DLQ configured on the queue (no `RedrivePolicy`), so even a message that *did* get retried on a genuine invocation-level failure would eventually be dropped without a safety net.

**What this would need to be production-safe:**
1. Enable `ReportBatchItemFailures` on the event source mapping, and have the handler return the specific failed message IDs instead of swallowing the exception.
2. Configure a DLQ with a `RedrivePolicy` (`maxReceiveCount`) on the queue, so repeatedly-failing messages land somewhere visible instead of disappearing.
3. Add a CloudWatch alarm on the DLQ's message count, so a failure actually gets noticed.

None of this is implemented today. Stating it here rather than letting an interviewer find it first.

---

## 7. Infrastructure as Code: CloudFormation, Not Terraform

Unlike the other Terraform-based projects in this portfolio, this one is provisioned with **AWS CloudFormation** — a deliberate choice to demonstrate comfort with AWS's native IaC tool, not just the third-party standard. IAM least-privilege roles are provisioned as part of the same template, scoped to exactly what the Lambda needs (SQS read/delete, DynamoDB write).

---

## 8. Risks and Trade-offs (Summary)

**DynamoDB vs RDS:** fits the single-key access pattern (`order_id` hash key, `PAY_PER_REQUEST`) and scales under bursty writes without capacity planning ahead of time; loses relational query flexibility.

**SQS vs Kinesis:** simpler model for a single-consumer, non-replay pipeline; no replay window or native fan-out. Queue is encrypted with a customer-managed KMS key, a direct response to a Trivy security finding.

**Batch processing:** amortizes Lambda invocation overhead at scale (`BatchSize: 10`); but without partial-failure reporting, this widens the blast radius of the gap below.

**Silent order loss (the real gap):** a per-record exception is caught and logged, not re-raised — the message is deleted from the queue regardless, and there's no DLQ to catch it. A DynamoDB throttle or write error today means a quietly lost order, not a retried one. This is the single most important thing to be ready to discuss about this project.

**Simulated eSIM generation:** the architecture (queueing, decoupling, storage) is real and load-bearing; the cryptographic provisioning step is not implemented and is explicitly out of scope, not hidden.

---

## Tech Stack

* **Infrastructure as Code:** AWS CloudFormation
* **Ingestion:** Amazon SQS (SSE-KMS, customer-managed key)
* **Compute:** AWS Lambda (Python 3.12)
* **Storage:** Amazon DynamoDB (`PAY_PER_REQUEST`)
* **Permissions:** AWS IAM (Least Privilege, scoped per-action)
