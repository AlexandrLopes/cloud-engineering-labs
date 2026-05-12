variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "admin"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
  default     = "admin123"
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "platform"
}