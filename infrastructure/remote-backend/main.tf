provider "aws" {
  region = "us-east-1"
}

# 1. Bucket S3 para guardar o arquivo de estado
resource "aws_s3_bucket" "terraform_state" {
  bucket        = "alexandre-labs-terraform-state-2026" # Lembre-se: Nomes de bucket S3 precisam ser únicos no mundo! Se der erro, coloque uns números aleatórios no final.
  force_destroy = true 
}

resource "aws_s3_bucket_versioning" "state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 2. Tabela DynamoDB para o State Lock
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID" 

  attribute {
    name = "LockID"
    type = "S"
  }
}