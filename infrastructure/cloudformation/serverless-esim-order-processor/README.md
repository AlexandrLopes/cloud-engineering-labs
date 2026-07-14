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

eSIM profile records are accessed almost exclusively by a single key (the order/ICCID identifier) — a lookup pattern, not relational querying across tables. [VALIDATE: confirm this matches your actual reasoning, or state the real one — e.g. "chosen for throughput under bursty write load without needing to size/provision a relational instance ahead of time."]

Contrast with `aws-3tier-infrastructure`, where the data is genuinely relational (users table with foreign-key-style relationships expected to grow) — DynamoDB there would fight the access pattern instead of fitting it.

**Trade-off accepted:** no ad-hoc relational queries (e.g. "all orders from customer X joined with billing") without a secondary index or a separate analytics path — DynamoDB isn't built for that.

---

## 4. Ingestion Buffer: SQS, Not Kinesis

**Decision: standard SQS queue for ingestion, not Kinesis Data Streams.**

Each order is processed independently and exactly the queue semantics needed are "buffer, then process once, then delete" — SQS's model. [VALIDATE: confirm, or state your real reason — e.g. "Kinesis is built for ordered, replayable streams with multiple consumers reading the same data; this pipeline has a single consumer and doesn't need replay or strict ordering across orders, so SQS's simpler model and pricing fit better."]

**Trade-off accepted:** no built-in replay (once a message is processed and deleted, it's gone — unlike Kinesis's retention window), and no fan-out to multiple independent consumers without additional plumbing (SNS+SQS fan-out pattern).

---

## 5. Processing: Lambda Batching, Not One-Invocation-Per-Message

Lambda is configured to pull **batches** of messages from SQS per invocation, not one message per invocation.

**Why it matters:** at high volume, one-invocation-per-message means one Lambda cold/warm start per order — batching amortizes that overhead across many orders per invocation, which is what actually delivers the "high-volume" part of the design, not just the queue by itself.

**Trade-off accepted:** a single bad record inside a batch can affect the whole batch's handling depending on the failure-handling configuration (partial batch failure reporting needs to be explicitly enabled — [VALIDATE: state whether this project enables `ReportBatchItemFailures`, or flag it as a known gap if not]).

---

## 6. Resilience

**If DynamoDB throttles:** the message is not deleted from SQS until Lambda successfully processes it. A throttled write means the message becomes visible again after the visibility timeout and is retried — no order is silently dropped.

**Dead-letter handling:** [VALIDATE: does this project have a DLQ configured for messages that fail repeatedly? If yes, describe the redrive policy; if not, state it as a known gap — a queue without a DLQ means a poison-pill message can retry forever or eventually be dropped at `maxReceiveCount`, silently, unless a DLQ is monitored.]

---

## 7. Infrastructure as Code: CloudFormation, Not Terraform

Unlike the other Terraform-based projects in this portfolio, this one is provisioned with **AWS CloudFormation** — a deliberate choice to demonstrate comfort with AWS's native IaC tool, not just the third-party standard. IAM least-privilege roles are provisioned as part of the same template, scoped to exactly what the Lambda needs (SQS read/delete, DynamoDB write).

---

## 8. Risks and Trade-offs (Summary)

**DynamoDB vs RDS:** fits the single-key access pattern and scales under bursty writes without capacity planning ahead of time; loses relational query flexibility.

**SQS vs Kinesis:** simpler model for a single-consumer, non-replay pipeline; no replay window or native fan-out.

**Batch processing:** amortizes Lambda invocation overhead at scale; a misconfigured batch-failure policy can affect more than the one bad record.

**Simulated eSIM generation:** the architecture (queueing, decoupling, storage) is real and load-bearing; the cryptographic provisioning step is not implemented and is explicitly out of scope, not hidden.

---

## Tech Stack

* **Infrastructure as Code:** AWS CloudFormation
* **Ingestion:** Amazon SQS
* **Compute:** AWS Lambda
* **Storage:** Amazon DynamoDB
* **Permissions:** AWS IAM (Least Privilege)
