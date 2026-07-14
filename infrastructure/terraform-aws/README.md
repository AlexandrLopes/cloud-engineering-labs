# AWS Production Environment

**Modular VPC, hardened EC2, and encrypted S3 — provisioned with Terraform, with the networking bug that would have made it unreachable found and fixed.**

## 1. Context and Objective

A minimal but hardened web server stack: isolated VPC, a hardened EC2 instance serving HTTP, and an encrypted S3 bucket — built to demonstrate secure defaults (IMDSv2, EBS encryption, restricted Security Groups), not to be a scaled production architecture (no load balancer, no multi-AZ, no autoscaling — see Section 5).

```
modules/network (VPC + subnet)
  -> aws_security_group (HTTP in, HTTPS/HTTP out)
  -> aws_instance (Amazon Linux 2023, IMDSv2 enforced, EBS encrypted)
  -> aws_s3_bucket (AES256, public access blocked)
```

---

## 2. The Gap This Closes: No Internet Gateway

**What the earlier version actually had:** a VPC and a public subnet with `map_public_ip_on_launch = true` — which assigns a public IP to any instance launched there, but does **not** create a path to the internet. There was no Internet Gateway, no route table, and no association between the subnet and any route. The EC2 instance would have deployed successfully, received a public IP, and been completely unreachable — `terraform apply` succeeds, `curl` to the public IP times out.

**Fixed:** the network module now provisions an `aws_internet_gateway`, a dedicated `aws_route_table` with a `0.0.0.0/0` route pointing at it, and an explicit `aws_route_table_association` binding the public subnet to that route table. This is the part that actually makes "public subnet" mean something — a public IP with no route is not public access.

---

## 3. Modular Networking: Why a Separate Module

**Decision: networking lives in `modules/network`, not inline in the root module.**

The VPC/subnet logic is self-contained and reusable — anything needing a VPC + public subnet with this shape can call the module with a different `project_name` and get an isolated network, without duplicating the VPC/subnet/IGW/route table resources inline. The root module (`terraform-aws`) consumes it via `module "networking" { source = "./modules/network" }` and reads `vpc_id`/`subnet_id` from its outputs.

**Trade-off accepted:** for a single-environment lab project, a module adds a layer of indirection that isn't strictly necessary — the payoff is in reusability across environments, which this project doesn't yet exercise (unlike `sip-ingress-aws`'s `environments/prod` and `environments/staging`, which actually instantiate the same modules twice with different variables).

---

## 4. Hardening

* **IMDSv2 enforced** (`http_tokens = "required"`) — mitigates SSRF-style credential theft via the instance metadata service.
* **EBS encrypted at rest** on the root volume.
* **Security Group scoped to what's needed:** inbound HTTP (80) only; outbound restricted to HTTPS (443, for package repo access) and HTTP (80) — no unrestricted egress.
* **S3 bucket:** `AES256` encryption by default, all four Block Public Access settings enabled.

**Trade-off, stated directly:** there's no SSH access defined anywhere in this stack, and the instance has no IAM instance profile — meaning there's no way to log into or manage this instance after it boots, by design or by oversight. If operational access were needed, the pattern used in `aws-3tier-infrastructure` (bastion host, SG-chained SSH) or `sip-ingress-aws` (ECS Exec, no SSH at all) would apply here; neither is implemented in this project.

---

## 5. Risks and Trade-offs (Summary)

**Missing Internet Gateway (fixed):** covered in Section 2 — this was a deploy-succeeds-but-doesn't-work bug, not a cosmetic gap.

**No SSH/SSM access path:** the instance boots and serves HTTP, but there's no way to access it afterward for debugging or updates beyond redeploying.

**S3 bucket provisioned but unused:** the bucket exists with correct hardening, but nothing in this stack reads from or writes to it — no IAM role connects the EC2 instance to the bucket. It's provisioned infrastructure, not yet a working part of the application.

**Hardcoded remote state target:** the `backend "s3"` block in `main.tf` points to a specific bucket name and DynamoDB table (`alexandre-labs-terraform-state-2026`, `terraform-state-locks`) that must already exist — provisioned by the separate `remote-backend` project (see that project's README for the bootstrap order this implies).

**Single AZ, no scaling, no load balancer:** appropriate for a hardening demonstration; not a production traffic-serving architecture despite the project name — see `aws-3tier-infrastructure` and `sip-ingress-aws` in this same portfolio for the availability patterns (Multi-AZ, autoscaling) this project doesn't implement.

---

## How to Deploy

**Prerequisite:** the `remote-backend` project must be deployed first — it creates the S3 bucket and DynamoDB table this project's Terraform state depends on.

```bash
terraform init
terraform plan
terraform apply
```

## Tech Stack

* **IaC:** Terraform (modular: root + `modules/network`)
* **Cloud:** AWS (VPC, Internet Gateway, EC2, S3)
* **OS:** Amazon Linux 2023
* **State:** S3 backend with DynamoDB locking (see `remote-backend`)
