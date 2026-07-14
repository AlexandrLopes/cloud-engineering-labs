provider "aws" {
  region = "us-east-1"
}

resource "aws_lambda_function" "remediation_bot" {
  filename      = "remediation.zip"
  function_name = "security-group-auto-remediation"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "remediation.lambda_handler"
  runtime       = "python3.9"
  timeout       = 10

  environment {
    variables = {
      LOG_LEVEL           = "INFO"
      ALLOWED_CIDR_RANGES = var.allowed_cidr_ranges
    }
  }
}

resource "aws_cloudwatch_event_rule" "detect_risky_sg_change" { #EventBridge Rule // Trigger
  name        = "detect-risky-sg-changes"
  description = "Trigger Lambda when a Security Group Ingress rule is created"

  #Filter
  event_pattern = <<EOF
{
  "source": ["aws.ec2"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["ec2.amazonaws.com"],
    "eventName": ["AuthorizeSecurityGroupIngress"]
  }
}
EOF
}

resource "aws_cloudwatch_event_target" "bind_lambda" {
  rule      = aws_cloudwatch_event_rule.detect_risky_sg_change.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.remediation_bot.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remediation_bot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.detect_risky_sg_change.arn
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "remediation-bot-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

#revoke SG rules
resource "aws_iam_role_policy" "lambda_policy" {
  name = "remediation-policy"
  role = aws_iam_role.lambda_exec_role.id

  # ec2:DescribeSecurityGroups removed — it was granted but never called
  # anywhere in remediation.py, which reads everything it needs directly
  # from the CloudTrail event payload. An unused permission is still a
  # permission an attacker gets if this role is ever compromised.

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "ec2:RevokeSecurityGroupIngress"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem"
        ],
        Resource = "arn:aws:dynamodb:us-east-1:*:table/SecurityAlerts"
      }
    ]
  })
}
