variable "project_name" {
  type        = string
  description = "Name of the project"
}

variable "environment" {
  type        = string
  description = "Environment name (e.g. dev, prod)"
}

variable "callback_urls" {
  type        = list(string)
  description = "List of allowed callback URLs"
  default     = ["http://localhost:3000/api/auth/callback/cognito"]
}

variable "logout_urls" {
  type        = list(string)
  description = "List of allowed logout URLs"
  default     = ["http://localhost:3000"]
}
