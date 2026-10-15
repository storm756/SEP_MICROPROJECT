terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Only used when running against a local AWS emulator (Floci/LocalStack)
  access_key                  = var.use_emulator ? "test" : null
  secret_key                  = var.use_emulator ? "test" : null
  skip_credentials_validation = var.use_emulator
  skip_metadata_api_check     = var.use_emulator
  skip_requesting_account_id  = var.use_emulator

  dynamic "endpoints" {
    for_each = var.use_emulator ? [1] : []
    content {
      ec2 = var.emulator_endpoint
      sts = var.emulator_endpoint
      iam = var.emulator_endpoint
      ssm = var.emulator_endpoint
    }
  }

  default_tags {
    tags = {
      Project     = "CityServe"
      Course      = "DevSecOps-Lab"
      ManagedBy   = "Terraform"
      Environment = "Production"
    }
  }
}
