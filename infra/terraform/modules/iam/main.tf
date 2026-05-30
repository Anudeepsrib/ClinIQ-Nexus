variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "documents_bucket_arn" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "sqs_queue_arns" {
  type    = list(string)
  default = []
}

variable "opensearch_domain_arn" {
  type    = string
  default = "*"
}

variable "secret_arns" {
  type    = list(string)
  default = []
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${var.project_name}-${var.environment}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_execution_secrets" {
  dynamic "statement" {
    for_each = length(var.secret_arns) > 0 ? [1] : []
    content {
      sid = "ReadTaskDefinitionSecrets"
      actions = [
        "secretsmanager:GetSecretValue",
      ]
      resources = var.secret_arns
    }
  }

  dynamic "statement" {
    for_each = length(var.secret_arns) > 0 ? [1] : []
    content {
      sid = "DecryptTaskDefinitionSecrets"
      actions = [
        "kms:Decrypt",
      ]
      resources = [var.kms_key_arn]
    }
  }
}

resource "aws_iam_policy" "ecs_execution_secrets" {
  count = length(var.secret_arns) > 0 ? 1 : 0

  name   = "${var.project_name}-${var.environment}-ecs-execution-secrets"
  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution_secrets" {
  count = length(var.secret_arns) > 0 ? 1 : 0

  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.ecs_execution_secrets[0].arn
}

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-${var.environment}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "ecs_task" {
  statement {
    sid = "DocumentsBucketAccess"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      var.documents_bucket_arn,
      "${var.documents_bucket_arn}/*",
    ]
  }

  statement {
    sid = "KmsUse"
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [var.kms_key_arn]
  }

  statement {
    sid = "BedrockInvoke"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = ["*"]
  }

  statement {
    sid = "OpenSearchAccess"
    actions = [
      "es:ESHttpGet",
      "es:ESHttpPost",
      "es:ESHttpPut",
    ]
    resources = [
      var.opensearch_domain_arn,
      "${var.opensearch_domain_arn}/*",
    ]
  }

  dynamic "statement" {
    for_each = length(var.sqs_queue_arns) > 0 ? [1] : []
    content {
      sid = "SqsWorkflowAccess"
      actions = [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
      ]
      resources = var.sqs_queue_arns
    }
  }
}

resource "aws_iam_policy" "ecs_task" {
  name   = "${var.project_name}-${var.environment}-ecs-task"
  policy = data.aws_iam_policy_document.ecs_task.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task.arn
}

output "ecs_execution_role_arn" {
  value = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}
