include "root" {
  path = "../../../root.hcl"
}

terraform {
  source = "../../../modules/vpc"
}

inputs = {
  environment = "dev"
  vpc_cidr    = "10.121.0.0/16"
  num_of_azs  = 2
  region      = "us-east-1"
}
