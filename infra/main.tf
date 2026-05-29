terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    # Configure via -backend-config or terraform.tfvars
    # bucket = "your-tf-state-bucket"
    # prefix = "synthlog"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
