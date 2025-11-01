include "root" {
  path = "../../../root.hcl"
}

terraform {
  source = "../../../modules/eks"
}

dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  environment              = "prod"
  region                   = "us-east-1"
  vpc_id                   = dependency.vpc.outputs.vpc_id
  subnet_ids               = dependency.vpc.outputs.public_subnet_ids
  control_plane_subnet_ids = dependency.vpc.outputs.public_subnet_ids
  eks_node_sizes           = ["t3.medium"]
  eks_version              = "1.28"
}
