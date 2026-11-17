# Proveedor AWS apuntando a la cuenta emulada con Floci. No hace falta tocarlo.
# Con Terraform instalado en tu equipo, Floci está en http://localhost:4566 (el valor por defecto).
# El corrector y los contenedores de la unidad le pasan otra dirección con -var floci=… o TF_VAR_floci.
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "floci" {
  description = "Dirección de Floci"
  type        = string
  default     = "http://localhost:4566"
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
    ec2 = var.floci
    iam = var.floci
    kms = var.floci
    rds = var.floci
    s3  = var.floci
    sts = var.floci
  }
}
