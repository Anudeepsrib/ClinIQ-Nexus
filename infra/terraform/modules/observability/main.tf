# CloudWatch Log Group for ECS / API
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/ecs/${var.project_name}-${var.environment}-api"
  retention_in_days = 90

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudTrail for Audit compliance
resource "aws_cloudtrail" "audit_trail" {
  name                          = "${var.project_name}-${var.environment}-audit"
  s3_bucket_name                = var.s3_bucket_name
  s3_key_prefix                 = "cloudtrail"
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::${var.s3_bucket_name}/"]
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
