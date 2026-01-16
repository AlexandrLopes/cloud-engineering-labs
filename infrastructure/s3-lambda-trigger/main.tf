provider "aws" {
  region = "us-east-1"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "incoming_bucket" {
  bucket        = "invoice-processor-${random_id.bucket_suffix.hex}"
  force_destroy = true # Allow destroy the bucket (Lab only)
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
          "dynamodb:PutItem"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.audit_table.arn
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_dynamo" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_dynamo_policy.arn
}