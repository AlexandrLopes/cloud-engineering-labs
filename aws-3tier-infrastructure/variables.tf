# variables.tf

variable "project_name" {
  description = "Nome do projeto, usado nos tags"
  type        = string
  default     = "three-tier-app"
}

variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block da VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR da subnet pública"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_app_subnet_cidr" {
  description = "CIDR da subnet privada do backend"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_db_subnet_cidr" {
  description = "CIDR da subnet privada do banco"
  type        = string
  default     = "10.0.3.0/24"
}

variable "allowed_ssh_cidr" {
  description = "Your IP address for SSH access to Bastion"
  type        = string
}