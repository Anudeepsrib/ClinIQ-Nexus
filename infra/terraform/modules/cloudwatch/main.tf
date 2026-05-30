variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "alb_arn_suffix" {
  type    = string
  default = ""
}

variable "ecs_cluster_name" {
  type    = string
  default = ""
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-${var.environment}-api"
  retention_in_days = var.environment == "prod" ? 365 : 90
  kms_key_id        = var.kms_key_arn

  tags = local.common_tags
}

variable "kms_key_arn" {
  type = string
}

resource "aws_cloudwatch_dashboard" "platform" {
  dashboard_name = "${var.project_name}-${var.environment}-platform"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name],
            [".", "MemoryUtilization", ".", "."],
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "ECS utilization"
        }
      }
    ]
  })
}

data "aws_region" "current" {}

output "api_log_group_name" {
  value = aws_cloudwatch_log_group.api.name
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.platform.dashboard_name
}
