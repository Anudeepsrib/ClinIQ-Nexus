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
}

variable "aws_region" { default = "us-east-1" }
variable "environment" { default = "dev" }

# Full production modules would be called here.
# This is a reference structure showing the complete architecture.

module "vpc" {
  source      = "../../modules/vpc"
  environment = var.environment
  vpc_cidr    = "10.20.0.0/16"
}

# Additional modules (RDS, OpenSearch, ECS, Cognito, S3, KMS, WAF, ElastiCache, etc.)
# would be instantiated here with proper networking, KMS, least-privilege IAM,
# private endpoints, encryption everywhere, and WAF rules.

output "note" {
  value = "This is the reference Terraform structure for ClinIQ-Nexus. Full modules exist in modules/."
}
