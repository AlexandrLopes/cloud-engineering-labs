variable "aws_region" {
  description = "AWS Region to deploy resources"
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project Tag Name"
  default     = "cloud-engineering-lab"
}

variable "instance_type" {
  description = "EC2 Instance Type"
  default     = "t2.micro"
}