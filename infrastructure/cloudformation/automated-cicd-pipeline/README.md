# Developer Enablement: Automated CI/CD Pipeline

**A standardized, self-service pipeline — a developer pushes code and it's built, tested, and deployed, with every stage and trade-off explicit.**

## 1. Context and Objective

Developers often spend days configuring infrastructure, permissions, and deployment scripts instead of writing application logic. This template eliminates that: a `git push` to CodeCommit triggers build and deployment automatically, on AWS-native services.

```
Developer push -> CodeCommit (Source) -> CodeBuild (Build) -> S3 (Deploy)
```

---

## 2. The Gap This Closes: Deploy Was Missing

**What the earlier version actually had:** a Source stage and a Build stage — CodeCommit and CodeBuild, wired correctly. But the pipeline stopped there. Calling that "CI/CD" was inaccurate: what existed was CI (build and test), with no CD (deploy) stage at all. A developer would `git push`, watch a build run, and the output would sit in the artifact bucket with nothing consuming it.

**Fixed:** a third stage, **Deploy**, now takes the build output and pushes it to a dedicated deployment bucket via CodePipeline's native S3 deploy action. This is the minimal, honest version of "deploy" for a template with no specific application defined yet — the artifact lands somewhere real, extractable, versioned, and ready to be served or picked up downstream (e.g. as a static site origin, or as an input to a further deployment target like ECS/Elastic Beanstalk in a less generic version of this template).

---

## 3. Artifact Storage: Two Buckets, Not One

**Decision: separate buckets for pipeline artifacts and deployed output.**

`PipelineArtifactBucket` holds CodePipeline's internal stage-to-stage handoff artifacts (Source output, Build output) — this is CodePipeline's own working storage, not meant to be a deployment target. `DeploymentBucket` is the actual destination the Deploy stage writes to. Keeping them separate avoids mixing CodePipeline's internal artifact versioning with what's meant to be consumed externally.

Both buckets carry the same hardening: `AES256` encryption by default, versioning enabled, and all four S3 Block Public Access settings on.

---

## 4. Permissions Model

**Decision: strict per-service IAM roles, scoped to exact resources.**

- **CodeBuild role:** can write logs and read/write only the artifact bucket — cannot touch CodeCommit, the deployment bucket, or anything else in the account.
- **CodePipeline role:** can read/write the artifact bucket, write (not read) the deployment bucket, pull from the specific CodeCommit repo, and start builds on the specific CodeBuild project — nothing broader.

Neither role has account-wide permissions on any service; every `Resource` in each policy is a specific ARN, not `*`.

---

## 5. Risks and Trade-offs (Summary)

**Deploy target is generic S3, not an application runtime:** this template deploys static build output to S3, not to a running service (ECS, EC2, Lambda). Appropriate for a static site or artifact repository; a real application deployment would need a different Deploy action (CodeDeploy, ECS deploy, CloudFormation deploy) depending on the target — the pipeline mechanics (Source → Build → Deploy, least-privilege roles) transfer directly, but the Deploy action's `Provider` and `Configuration` would change.

**No test gating before deploy:** CodeBuild runs whatever `buildspec.yml` the repo defines, but the pipeline doesn't have an explicit manual-approval or test-gate stage between Build and Deploy — a failing test inside the build would fail the CodeBuild stage and stop the pipeline (CodePipeline's default behavior), but there's no separate "Test" stage visible in the pipeline structure itself.

**No rollback mechanism:** if a bad deploy reaches the deployment bucket, there's no automated rollback — S3 versioning means the previous object version is recoverable manually, but nothing automates reverting to it.

---

## Tech Stack

* **Infrastructure as Code:** AWS CloudFormation
* **Source Control:** AWS CodeCommit
* **Build:** AWS CodeBuild
* **Orchestration:** AWS CodePipeline
* **Artifact Storage:** Amazon S3 (encrypted, versioned, no public access)
* **Permissions:** AWS IAM (least privilege, per-service roles)
