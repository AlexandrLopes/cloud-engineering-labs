provider "aws" {
  region = "us-east-1"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

variable "alert_email" {
  description = "Email to recieve alerts"
  default     = "alexandre.w.d.lopes@gmail.com"
}

resource "aws_s3_bucket" "incoming_bucket" {
  bucket        = "invoice-processor-${random_id.bucket_suffix.hex}"
  force_destroy = true #Labs only
}

resource "aws_s3_bucket_server_side_encryption_configuration" "incoming_bucket_encryption" {
  bucket = aws_s3_bucket.incoming_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "incoming_bucket_access" {
  bucket = aws_s3_bucket.incoming_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "processor.py"
  output_path = "processor_payload.zip"
}

resource "aws_lambda_function" "processor_lambda" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "S3_Event_Processor"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "processor.handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.security_alerts.arn
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.incoming_bucket.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.incoming_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "lambda_s3_processor_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

output "bucket_name" {
  value = aws_s3_bucket.incoming_bucket.id
}

resource "aws_dynamodb_table" "audit_table" {
  name         = "S3_File_Audit_Log"
  billing_mode = "PAY_PER_REQUEST" # Serverless (free to test)
  hash_key     = "file_name"

  attribute {
    name = "file_name"
    type = "S" # String
  }
}

resource "aws_iam_policy" "lambda_dynamo_policy" {
  name        = "lambda_dynamo_write_access"
  description = "Allows Lambda to write to DynamoDB"


  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "sns:Publish",
          "s3:GetObject"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_dynamo" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_dynamo_policy.arn
}

# SNS TOPIC
resource "aws_sns_topic" "security_alerts" {
  name              = "s3-security-alerts-topic"
  kms_master_key_id = "alias/aws/sns"
}

resource "aws_sns_topic_subscription" "email_target" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}