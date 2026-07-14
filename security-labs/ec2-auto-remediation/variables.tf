variable "allowed_cidr_ranges" {
  description = "Comma-separated CIDR ranges (e.g. corporate VPN) exempt from auto-remediation. Empty by default — every public rule is revoked unless explicitly allowlisted."
  type        = string
  default     = ""
}
