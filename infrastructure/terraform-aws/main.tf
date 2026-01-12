# ---------------------------------------------------------
# AWS Infrastructure Definition
# Project: Secure Network Foundation
# Author: Alexandr Lopes
# ---------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}

# 1. Create a Virtual Private Cloud (The Network)
resource "aws_vpc" "main_lab_vpc" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name        = "cloud-engineering-lab-vpc"
    Environment = "Production"
  }
}

# 2. Create a Security Group (The Firewall)
# This is what our Python script audits!
resource "aws_security_group" "web_server_sg" {
  name        = "web-server-sg"
  description = "Security Group for Web Servers"
  vpc_id      = aws_vpc.main_lab_vpc.id

  # Inbound Rule: Allow HTTP (Safe)
  ingress {
    description = "Allow HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Inbound Rule: Allow SSH (Restricted - GOOD PRACTICE)
  ingress {
    description = "Allow SSH only from Admin IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["187.15.30.0/32"] # Exemplo de IP fixo, não 0.0.0.0/0
  }

  tags = {
    Name = "secure-web-sg"
  }
}