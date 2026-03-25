# Developer Enablement: Automated CI/CD Pipeline

## Overview
A Platform Engineering solution designed to improve Developer Experience (DevEx) and reduce time-to-market. This AWS CloudFormation template provisions a fully automated, serverless CI/CD pipeline using AWS-native developer tools.

## The "Enablement" Problem Solved
Developers often spend days configuring infrastructure, permissions, and deployment scripts instead of writing application logic. This project eliminates that friction. By deploying this template, a developer instantly receives a standardized, secure repository connected to an automated build and deployment pipeline. They just need to `git push`.

## Architecture & Tech Stack
* **AWS CodeCommit:** A secure, highly scalable Git repository for the application source code.
* **AWS CodeBuild:** A fully managed continuous integration service that compiles source code and runs tests without the need to manage build servers.
* **AWS CodePipeline:** The orchestrator that automates the release process for fast and reliable application updates.
* **Amazon S3:** Acts as the secure Artifact Store.

## DevSecOps & Compliance
* **Strict Least Privilege:** Both CodeBuild and CodePipeline operate under highly restricted IAM Roles.
* **Secure Artifact Storage:** The S3 bucket holding the build artifacts enforces `AES256` Server-Side Encryption, Versioning, and strict Block Public Access policies (Trivy compliant).