output "log_group_name" {
  value = aws_cloudwatch_log_group.api_logs.name
}

output "cloudtrail_arn" {
  value = aws_cloudtrail.audit_trail.arn
}
