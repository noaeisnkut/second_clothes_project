include "root" {
  path = "../../../root.hcl"
}

terraform {
  source = "../../../modules/vpc"
}

inputs = {
  environment = "prod"
  vpc_cidr    = "10.120.0.0/16"
  num_of_azs  = 2
  region      = "us-east-1"
}
