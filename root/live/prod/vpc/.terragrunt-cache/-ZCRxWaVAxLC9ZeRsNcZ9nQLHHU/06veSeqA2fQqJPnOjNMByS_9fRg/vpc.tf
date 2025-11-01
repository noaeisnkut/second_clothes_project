module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.environment}-vpc"

  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.azs.names, 0, var.num_of_azs)
  private_subnets = [for i in range(var.num_of_azs) : cidrsubnet(var.vpc_cidr, 6, i)]
  public_subnets  = [for i in range(var.num_of_azs) : cidrsubnet(var.vpc_cidr, 6, 5 + i)]
  intra_subnets   = [for i in range(var.num_of_azs) : cidrsubnet(var.vpc_cidr, 6, 10 + i)]
  map_public_ip_on_launch = true

  enable_nat_gateway = true
  enable_vpn_gateway = false
  single_nat_gateway = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }


  tags = {
    Terraform   = "true"
    Environment = var.environment
  }
}