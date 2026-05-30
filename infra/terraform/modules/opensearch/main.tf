data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t3.medium.search"
}

variable "instance_count" {
  type    = number
  default = 2
}

variable "master_user_arn" {
  type    = string
  default = null
}

locals {
  domain_name = substr("${var.project_name}-${var.environment}-os", 0, 28)
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    HIPAA       = "true"
    ManagedBy   = "terraform"
  }
}

data "aws_iam_policy_document" "domain_access" {
  statement {
    actions = [
      "es:ESHttpGet",
      "es:ESHttpPost",
      "es:ESHttpPut",
      "es:ESHttpDelete",
    ]

    resources = [
      "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${local.domain_name}/*",
    ]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
}

resource "aws_opensearch_domain" "cluster" {
  domain_name    = local.domain_name
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = var.instance_type
    instance_count         = var.instance_count
    zone_awareness_enabled = var.instance_count > 1

    dynamic "zone_awareness_config" {
      for_each = var.instance_count > 1 ? [1] : []
      content {
        availability_zone_count = min(length(var.subnet_ids), var.instance_count, 3)
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 50
    volume_type = "gp3"
  }

  vpc_options {
    subnet_ids         = slice(var.subnet_ids, 0, min(length(var.subnet_ids), var.instance_count))
    security_group_ids = [var.security_group_id]
  }

  encrypt_at_rest {
    enabled    = true
    kms_key_id = var.kms_key_arn
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = false
    anonymous_auth_enabled         = false

    master_user_options {
      master_user_arn = coalesce(var.master_user_arn, "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root")
    }
  }

  access_policies = data.aws_iam_policy_document.domain_access.json

  tags = merge(local.common_tags, {
    Name = local.domain_name
  })
}

output "domain_id" {
  value = aws_opensearch_domain.cluster.domain_id
}

output "domain_arn" {
  value = aws_opensearch_domain.cluster.arn
}

output "domain_endpoint" {
  value = aws_opensearch_domain.cluster.endpoint
}
