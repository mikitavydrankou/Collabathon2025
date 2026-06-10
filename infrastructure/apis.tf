# GCP APIs the stack needs. Enabling is idempotent; we keep the services on
# `terraform destroy` (disable_on_destroy=false) so tearing down the cluster
# doesn't disrupt anything else in the project that relies on the same APIs.
locals {
  required_apis = [
    "compute.googleapis.com",          # VPC, the nodes Autopilot runs on
    "container.googleapis.com",        # GKE
    "artifactregistry.googleapis.com", # image registry
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.required_apis)

  service            = each.value
  disable_on_destroy = false
}
