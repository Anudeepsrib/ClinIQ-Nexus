terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "careos"
}

variable "environment" {
  type    = string
  default = "stage"
}

variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

variable "allowed_http_cidrs" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "db_name" {
  type    = string
  default = "careos"
}

variable "db_username" {
  type    = string
  default = "careosadmin"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "platform_api_image" {
  type        = string
  default     = ""
  description = "Optional prebuilt platform-api container image. Defaults to this environment's ECR repository :latest tag."
}

variable "alb_certificate_arn" {
  type        = string
  default     = ""
  description = "Optional ACM certificate ARN for HTTPS on the public ALB."
}

variable "alb_origin_url" {
  type        = string
  default     = ""
  description = "Optional full ALB origin URL for API Gateway, for example https://api-origin.stage.example.com."
}

variable "callback_urls" {
  type    = list(string)
  default = ["https://stage.careos.example.com/api/auth/callback/cognito"]
}

variable "logout_urls" {
  type    = list(string)
  default = ["https://stage.careos.example.com"]
}

variable "cors_allowed_origins" {
  type    = list(string)
  default = ["https://stage.careos.example.com"]
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Application = "careOS"
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  az_count           = var.az_count
  enable_nat_gateway = true
}

module "kms" {
  source       = "../../modules/kms"
  project_name = var.project_name
  environment  = var.environment
}

module "security" {
  source             = "../../modules/security"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  allowed_http_cidrs = var.allowed_http_cidrs
}

module "networking" {
  source                  = "../../modules/networking"
  project_name            = var.project_name
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  vpc_cidr_block          = module.vpc.vpc_cidr_block
  private_subnet_ids      = module.vpc.private_subnet_ids
  private_route_table_ids = module.vpc.private_route_table_ids
}

module "s3" {
  source       = "../../modules/s3"
  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.kms.key_arn
}

module "sqs" {
  source       = "../../modules/sqs"
  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.kms.key_arn
}

module "opensearch" {
  source            = "../../modules/opensearch"
  project_name      = var.project_name
  environment       = var.environment
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_id = module.security.opensearch_security_group_id
  kms_key_arn       = module.kms.key_arn
  instance_type     = "t3.medium.search"
  instance_count    = 2
}

module "rds" {
  source              = "../../modules/rds"
  project_name        = var.project_name
  environment         = var.environment
  database_subnet_ids = module.vpc.database_subnet_ids
  security_group_id   = module.security.rds_security_group_id
  kms_key_arn         = module.kms.key_arn
  db_name             = var.db_name
  db_username         = var.db_username
  db_password         = var.db_password
  instance_class      = "db.t4g.medium"
  allocated_storage   = 100
  multi_az            = true
}

module "redis" {
  source             = "../../modules/redis"
  project_name       = var.project_name
  environment        = var.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security.redis_security_group_id
  kms_key_arn        = module.kms.key_arn
  node_type          = "cache.t4g.small"
}

module "secrets" {
  source       = "../../modules/secrets-manager"
  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.kms.key_arn
  db_username  = var.db_username
  db_password  = var.db_password
  db_endpoint  = module.rds.db_endpoint
  db_port      = module.rds.db_port
  db_name      = module.rds.db_name
}

module "iam" {
  source                = "../../modules/iam"
  project_name          = var.project_name
  environment           = var.environment
  documents_bucket_arn  = module.s3.documents_bucket_arn
  kms_key_arn           = module.kms.key_arn
  sqs_queue_arns        = module.sqs.queue_arns
  opensearch_domain_arn = module.opensearch.domain_arn
  secret_arns           = module.secrets.secret_arns
}

module "cloudwatch" {
  source           = "../../modules/cloudwatch"
  project_name     = var.project_name
  environment      = var.environment
  kms_key_arn      = module.kms.key_arn
  ecs_cluster_name = "${var.project_name}-${var.environment}-cluster"
}

module "cognito" {
  source        = "../../modules/cognito"
  project_name  = var.project_name
  environment   = var.environment
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls
}

module "ecs" {
  source                = "../../modules/ecs"
  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  private_subnet_ids    = module.vpc.private_subnet_ids
  alb_security_group_id = module.security.alb_security_group_id
  app_security_group_id = module.security.app_security_group_id
  execution_role_arn    = module.iam.ecs_execution_role_arn
  task_role_arn         = module.iam.ecs_task_role_arn
  log_group_name        = module.cloudwatch.api_log_group_name
  container_image       = var.platform_api_image
  certificate_arn       = var.alb_certificate_arn
  desired_count         = 2
  cpu                   = 1024
  memory                = 2048

  environment_variables = {
    AUDIT_LOG_BUCKET        = module.s3.audit_bucket_id
    AWS_REGION              = var.aws_region
    COGNITO_APP_CLIENT_ID   = module.cognito.user_pool_client_id
    COGNITO_REGION          = var.aws_region
    COGNITO_USER_POOL_ID    = module.cognito.user_pool_id
    ENVIRONMENT             = var.environment
    OPENSEARCH_ENDPOINT     = "https://${module.opensearch.domain_endpoint}"
    OTEL_SERVICE_NAME       = "careos-platform-api"
    REDIS_URL               = "rediss://${module.redis.primary_endpoint}:6379/0"
    S3_DOCUMENT_BUCKET      = module.s3.documents_bucket_id
    SQS_INGESTION_QUEUE_URL = module.sqs.ingestion_queue_url
    SQS_WORKFLOW_QUEUE_URL  = module.sqs.workflow_queue_url
    USE_REAL_AWS            = "true"
  }

  secret_environment_variables = {
    DATABASE_URL = module.secrets.database_url_secret_arn
  }
}

module "waf" {
  source       = "../../modules/waf"
  project_name = var.project_name
  environment  = var.environment
  alb_arn      = module.ecs.alb_arn
}

module "api_gateway" {
  source               = "../../modules/api-gateway"
  project_name         = var.project_name
  environment          = var.environment
  alb_dns_name         = module.ecs.alb_dns_name
  alb_origin_url       = var.alb_origin_url
  kms_key_arn          = module.kms.key_arn
  cors_allowed_origins = var.cors_allowed_origins
}

module "observability" {
  source                 = "../../modules/observability"
  project_name           = var.project_name
  environment            = var.environment
  s3_bucket_name         = module.s3.audit_bucket_id
  kms_key_arn            = module.kms.key_arn
  data_event_bucket_arns = [module.s3.documents_bucket_arn, module.s3.audit_bucket_arn]
}

module "eventbridge" {
  source             = "../../modules/eventbridge"
  project_name       = var.project_name
  environment        = var.environment
  workflow_queue_arn = module.sqs.workflow_queue_arn
  workflow_queue_url = module.sqs.workflow_queue_url
}

output "api_endpoint" {
  value = module.api_gateway.api_endpoint
}

output "alb_dns_name" {
  value = module.ecs.alb_dns_name
}

output "cognito_user_pool_id" {
  value = module.cognito.user_pool_id
}

output "documents_bucket" {
  value = module.s3.documents_bucket_id
}

output "ecr_repository_url" {
  value = module.ecs.ecr_repository_url
}

output "opensearch_endpoint" {
  value = module.opensearch.domain_endpoint
}

output "rds_endpoint" {
  value = module.rds.db_endpoint
}

output "redis_endpoint" {
  value = module.redis.primary_endpoint
}
