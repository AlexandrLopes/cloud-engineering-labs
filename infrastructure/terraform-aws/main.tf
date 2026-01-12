# ---------------------------------------------------------
# AWS Infrastructure Definition - The "Holy Trinity"
# Compute (EC2) + Network (VPC) + Storage (S3)
# Author: Alexandre Lopes
# ---------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}


# 1. NETWORKING 

resource "aws_vpc" "main_lab_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "cloud-engineering-lab-vpc" }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.main_lab_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  tags = { Name = "public-subnet-1" }
}


# 2. SECURITY 

resource "aws_security_group" "web_sg" {
  name        = "web-server-sg"
  description = "Allow HTTP and SSH"
  vpc_id      = aws_vpc.main_lab_vpc.id

  ingress {
    description = "HTTP Public Access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# 3. COMPUTE 

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "web_server" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Deployed via Terraform by Alexandr Lopes</h1>" > /var/www/html/index.html
              EOF

  tags = { Name = "Terraform-Automated-Server" }
}


# 4. STORAGE 


# Gets a random code for the unique name (ex: ab12cd) 
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "project_bucket" {
  bucket = "cloud-labs-storage-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name        = "Project Data"
    Environment = "Production"
  }
}

# Allow version control (Data security)
resource "aws_s3_bucket_versioning" "versioning_example" {
  bucket = aws_s3_bucket.project_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}


# OUTPUTS 

output "server_public_ip" {
  value = aws_instance.web_server.public_ip
  description = "The public IP address of the web server"
}

output "s3_bucket_name" {
  value = aws_s3_bucket.project_bucket.id
  description = "The unique name of the S3 bucket created"
}