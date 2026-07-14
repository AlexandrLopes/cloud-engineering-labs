resource "random_id" "backup_bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "backup" {
  bucket = "${var.project_name}-backup-${random_id.backup_bucket_suffix.hex}"

  tags = {
    Name    = "${var.project_name}-backup"
    Project = var.project_name
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup_encryption" {
  bucket = aws_s3_bucket.backup.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "backup_access" {
  bucket = aws_s3_bucket.backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "backup_versioning" {
  bucket = aws_s3_bucket.backup.id

  versioning_configuration {
    status = "Enabled"
  }
}
