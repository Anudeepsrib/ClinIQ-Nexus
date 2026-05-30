variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "function_name" {
  type        = string
  description = "Short function purpose, for example ingestion-worker."
}

variable "image_uri" {
  type        = string
  description = "ECR image URI for the Lambda container image."
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "kms_key_arn" {
  type = string
}

variable "timeout_seconds" {
  type    = number
  default = 60
}

variable "memory_size_mb" {
  type    = number
  default = 1024
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

locals {
  full_name = "${var.project_name}-${var.environment}-${var.function_name}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.full_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "vpc_execution" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.full_name}"
  retention_in_days = var.environment == "prod" ? 365 : 90
  kms_key_id        = var.kms_key_arn
  tags              = local.common_tags
}

resource "aws_lambda_function" "worker" {
  function_name = local.full_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  timeout       = var.timeout_seconds
  memory_size   = var.memory_size_mb
  kms_key_arn   = var.kms_key_arn

  environment {
    variables = var.environment_variables
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = local.common_tags
}

output "function_name" {
  value = aws_lambda_function.worker.function_name
}

output "function_arn" {
  value = aws_lambda_function.worker.arn
}

output "role_arn" {
  value = aws_iam_role.lambda.arn
}
