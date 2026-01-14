provider "aws" {
  region = "us-east-1"
}

# terraform will zip the file 
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function_payload.zip"
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "serverless_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_lambda_function" "test_lambda" {
  
  filename      = data.archive_file.lambda_zip.output_path
  
  
  function_name = "Terraform_Python_Automation"
  
  
  role          = aws_iam_role.iam_for_lambda.arn
  
  
  handler       = "lambda_function.lambda_handler"
  
  
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  runtime = "python3.9"
}

output "lambda_name" {
  value = aws_lambda_function.test_lambda.function_name
}