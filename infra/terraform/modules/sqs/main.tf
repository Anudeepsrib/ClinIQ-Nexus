variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

resource "aws_sqs_queue" "ingestion_dlq" {
  name              = "${var.project_name}-${var.environment}-ingestion-dlq"
  kms_master_key_id = var.kms_key_arn
  tags              = local.common_tags
}

resource "aws_sqs_queue" "ingestion" {
  name                       = "${var.project_name}-${var.environment}-ingestion"
  visibility_timeout_seconds = 900
  message_retention_seconds  = 1209600
  kms_master_key_id          = var.kms_key_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = 3
  })

  tags = local.common_tags
}

resource "aws_sqs_queue" "workflow_dlq" {
  name              = "${var.project_name}-${var.environment}-workflow-dlq"
  kms_master_key_id = var.kms_key_arn
  tags              = local.common_tags
}

resource "aws_sqs_queue" "workflow" {
  name                       = "${var.project_name}-${var.environment}-workflow"
  visibility_timeout_seconds = 900
  message_retention_seconds  = 1209600
  kms_master_key_id          = var.kms_key_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.workflow_dlq.arn
    maxReceiveCount     = 3
  })

  tags = local.common_tags
}

output "ingestion_queue_arn" {
  value = aws_sqs_queue.ingestion.arn
}

output "ingestion_queue_url" {
  value = aws_sqs_queue.ingestion.url
}

output "workflow_queue_arn" {
  value = aws_sqs_queue.workflow.arn
}

output "workflow_queue_url" {
  value = aws_sqs_queue.workflow.url
}

output "queue_arns" {
  value = [
    aws_sqs_queue.ingestion.arn,
    aws_sqs_queue.workflow.arn,
  ]
}
