terraform {
  required_version = ">= 1.7"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Remote state lives in a GCS bucket so the cluster isn't owned by one laptop.
  # The bucket must exist before `terraform init` (chicken-and-egg: it can't be
  # created by this same state). Create it once by hand, then uncomment:
  #
  #   gcloud storage buckets create gs://easyfocus-tfstate-<project> \
  #     --location=europe-central2 --uniform-bucket-level-access
  #
  # backend "gcs" {
  #   bucket = "easyfocus-tfstate-<project>"
  #   prefix = "gke"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
