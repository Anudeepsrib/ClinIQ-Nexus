# Production-grade VPC module for ClinIQ-Nexus (simplified reference)
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "environment" { type = string }
variable "vpc_cidr" { type = string }

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "cliniq-${var.environment}"
    Environment = var.environment
    Project     = "ClinIQ-Nexus"
    HIPAA       = "true"
  }
}

# Public + private subnets + NAT would go here in full module
output "vpc_id" { value = aws_vpc.main.id }
