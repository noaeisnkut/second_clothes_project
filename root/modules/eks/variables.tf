variable "environment" {
  type        = string
  description = "Environment name (dev/prod)"
}

variable "region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}
variable "eks_version" {
  type = string
  default = "1.29"
  description = "version of eks"
}
variable "eks_node_sizes" {
  type = list(string)
  description = "size of eks nodes"
  default =["t3.medium"]
}
variable "vpc_id" {
  description = "VPC ID for the EKS cluster"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets IDs for the EKS cluster"
  type        = list(string)
}

variable "control_plane_subnet_ids" {
  description = "Control plane subnet IDs for the EKS cluster"
  type        = list(string)
}
