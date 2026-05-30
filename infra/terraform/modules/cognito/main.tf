resource "aws_cognito_user_pool" "pool" {
  name = "${var.project_name}-${var.environment}-pool"

  mfa_configuration          = var.environment == "prod" ? "ON" : "OPTIONAL"
  auto_verified_attributes   = ["email"]
  username_attributes        = ["email"]
  deletion_protection        = var.environment == "prod" ? "ACTIVE" : "INACTIVE"
  user_pool_tier             = "ESSENTIALS"
  email_verification_subject = "Verify your MediCore AI account"
  email_verification_message = "Your verification code is {####}."

  software_token_mfa_configuration {
    enabled = true
  }

  password_policy {
    minimum_length    = 14
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "tenant_id"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "role"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "assigned_patients"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "consent_scopes"
    required            = false
    mutable             = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "${var.project_name}-${var.environment}-client"
  user_pool_id = aws_cognito_user_pool.pool.id

  generate_secret = true
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  callback_urls                        = var.callback_urls
  logout_urls                          = var.logout_urls
  prevent_user_existence_errors        = "ENABLED"
  refresh_token_validity               = 8
  access_token_validity                = 60
  id_token_validity                    = 60
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  supported_identity_providers         = ["COGNITO"]

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "hours"
  }
}

resource "aws_cognito_user_pool_domain" "domain" {
  domain       = "${var.project_name}-${var.environment}-auth"
  user_pool_id = aws_cognito_user_pool.pool.id
}
