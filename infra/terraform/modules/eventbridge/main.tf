variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "workflow_queue_arn" {
  type = string
}

variable "workflow_queue_url" {
  type = string
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_event_bus" "platform" {
  name = "${var.project_name}-${var.environment}-bus"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_rule" "workflow_sweeper" {
  name                = "${var.project_name}-${var.environment}-workflow-sweeper"
  description         = "Periodic workflow maintenance trigger"
  schedule_expression = "rate(15 minutes)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "workflow_queue" {
  rule = aws_cloudwatch_event_rule.workflow_sweeper.name
  arn  = var.workflow_queue_arn
}

data "aws_iam_policy_document" "events_to_sqs" {
  statement {
    actions   = ["sqs:SendMessage"]
    resources = [var.workflow_queue_arn]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_sqs_queue_policy" "workflow_events" {
  queue_url = var.workflow_queue_url
  policy    = data.aws_iam_policy_document.events_to_sqs.json
}

output "event_bus_name" {
  value = aws_cloudwatch_event_bus.platform.name
}

output "workflow_sweeper_rule_arn" {
  value = aws_cloudwatch_event_rule.workflow_sweeper.arn
}
