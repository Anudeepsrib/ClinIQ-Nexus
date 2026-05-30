output "user_pool_id" {
  value       = aws_cognito_user_pool.pool.id
  description = "The ID of the Cognito User Pool"
}

output "user_pool_client_id" {
  value       = aws_cognito_user_pool_client.client.id
  description = "The ID of the Cognito User Pool Client"
}

output "user_pool_client_secret" {
  value       = aws_cognito_user_pool_client.client.client_secret
  description = "The client secret of the Cognito User Pool Client"
  sensitive   = true
}

output "cognito_domain" {
  value       = aws_cognito_user_pool_domain.domain.domain
  description = "The Cognito domain prefix"
}
