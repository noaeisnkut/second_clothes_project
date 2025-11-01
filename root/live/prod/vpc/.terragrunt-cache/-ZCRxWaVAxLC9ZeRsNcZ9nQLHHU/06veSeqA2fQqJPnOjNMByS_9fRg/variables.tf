variable "environment" {
  type        = string
  description = "Environment name (dev/prod)"
}

variable "vpc_cidr" {
  type = string
  default = "10.120.0.0/16"
  description = "CIDR block of the environment"
}

variable "num_of_azs" {
  type = number
  default = 1
  description = "how many azs in our vpc"
}

variable "region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}
