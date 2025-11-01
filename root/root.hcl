remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = "second-clothes-project-terraform-state-4321"
    region         = "us-east-1"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    dynamodb_table = "second-clothes-project-tf-lock"
    encrypt        = true
  }
}

inputs = {
  aws_region   = "us-east-1"
  project_name = "second-clothes-app"
}
