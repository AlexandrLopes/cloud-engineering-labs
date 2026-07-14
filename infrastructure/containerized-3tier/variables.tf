variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "admin"
}

variable "postgres_password" {
  description = "PostgreSQL password. No default on purpose — this must be supplied via terraform.tfvars or -var, never committed to the repo."
  type        = string
  sensitive   = true
  # No default. `sensitive = true` only hides the value from Terraform's own
  # CLI output — it does nothing to protect a value that's sitting in this
  # file in plaintext. The previous version had `default = "admin123"`
  # committed here, which defeats the purpose of marking it sensitive at all.
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "platform"
}
