# Proveedor AWS apuntando a la cuenta emulada con Floci. No tocar en esta práctica.
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "eu-west-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = "http://floci:4566"
    iam = "http://floci:4566"
    s3  = "http://floci:4566"
    sts = "http://floci:4566"
  }
}
