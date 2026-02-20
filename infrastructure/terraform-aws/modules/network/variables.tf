variable "project_name" {
  description = "O nome do projeto que vem do arquivo principal"
  type        = string
}

variable "vpc_cidr" {
  description = "O bloco CIDR da VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "O bloco CIDR da Subnet"
  type        = string
  default     = "10.0.1.0/24"
}