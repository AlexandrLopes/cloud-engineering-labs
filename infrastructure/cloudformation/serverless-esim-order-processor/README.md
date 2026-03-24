# Serverless High-Volume eSIM Order Processor

## Overview
An event-driven, serverless architecture designed to process high volumes of eSIM activation orders asynchronously. Built entirely with **AWS CloudFormation**, this project demonstrates how to decouple ingestion from processing using message queues, preventing database bottlenecks during traffic spikes (e.g., Black Friday sales).

## Architecture (Decoupled Flow)
1. **Amazon SQS (Ingestion):** Acts as a buffer. Receives thousands of incoming eSIM activation requests concurrently without overwhelming the system.
2. **AWS Lambda (Processing):** Triggered automatically by SQS. It pulls batches of messages, simulates the cryptographic generation of the eSIM profile (ICCID), and prepares the data.
3. **Amazon DynamoDB (Storage):** A highly scalable NoSQL database that stores the successfully generated active eSIM profiles.

## Business Value
* **Resilience:** If the database experiences throttling, messages remain safely in the SQS queue until they can be processed. Zero dropped orders.
* **Cost Efficiency:** Serverless execution means we pay only for the exact compute time used to process the orders, avoiding the cost of idle EC2 instances.
* **Infrastructure as Code:** The entire architecture, including IAM Least Privilege roles, is provisioned dynamically via a single CloudFormation template.