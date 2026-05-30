variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "s3_bucket_name" {
  type        = string
  description = "Bucket for CloudTrail logs"
}

variable "kms_key_arn" {
  type        = string
  description = "KMS key for CloudTrail encryption"
}

variable "data_event_bucket_arns" {
  type        = list(string)
  default     = []
  description = "S3 bucket ARNs to include in CloudTrail object data events."
}

locals {
  data_event_values = length(var.data_event_bucket_arns) > 0 ? [
    for bucket_arn in var.data_event_bucket_arns : "${bucket_arn}/"
  ] : ["arn:aws:s3:::${var.s3_bucket_name}/"]
}

resource "aws_cloudtrail" "audit_trail" {
  name                          = "${var.project_name}-${var.environment}-audit"
  s3_bucket_name                = var.s3_bucket_name
  s3_key_prefix                 = "cloudtrail"
  kms_key_id                    = var.kms_key_arn
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = local.data_event_values
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

output "cloudtrail_arn" {
  value = aws_cloudtrail.audit_trail.arn
}
