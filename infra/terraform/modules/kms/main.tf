data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "deletion_window_in_days" {
  type    = number
  default = 30
}

locals {
  service_principals = [
    "cloudtrail.amazonaws.com",
    "elasticache.amazonaws.com",
    "logs.${data.aws_region.current.name}.amazonaws.com",
    "opensearchservice.amazonaws.com",
    "rds.amazonaws.com",
    "s3.amazonaws.com",
    "secretsmanager.amazonaws.com",
    "sqs.amazonaws.com",
  ]

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

data "aws_iam_policy_document" "platform_key" {
  statement {
    sid = "EnableAccountKeyAdministration"
    actions = [
      "kms:*",
    ]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    sid = "AllowPlatformServiceKeyUse"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:ReEncryptFrom",
      "kms:ReEncryptTo",
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = local.service_principals
    }
  }

  statement {
    sid = "AllowPlatformServiceGrants"
    actions = [
      "kms:CreateGrant",
      "kms:ListGrants",
      "kms:RevokeGrant",
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = local.service_principals
    }

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

resource "aws_kms_key" "platform" {
  description             = "${var.project_name}-${var.environment} platform encryption key"
  deletion_window_in_days = var.deletion_window_in_days
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.platform_key.json

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-platform-kms"
  })
}

resource "aws_kms_alias" "platform" {
  name          = "alias/${var.project_name}-${var.environment}-platform"
  target_key_id = aws_kms_key.platform.key_id
}

output "key_id" {
  value = aws_kms_key.platform.key_id
}

output "key_arn" {
  value = aws_kms_key.platform.arn
}

output "alias_name" {
  value = aws_kms_alias.platform.name
}
