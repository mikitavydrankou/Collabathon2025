output "cluster_name" {
  description = "GKE cluster name — feed to `gcloud container clusters get-credentials`."
  value       = google_container_cluster.autopilot.name
}

output "cluster_location" {
  description = "Region the cluster lives in."
  value       = google_container_cluster.autopilot.location
}

output "get_credentials_command" {
  description = "Copy-paste to point kubectl at the new cluster."
  value       = "gcloud container clusters get-credentials ${google_container_cluster.autopilot.name} --region ${var.region} --project ${var.project_id}"
}

output "artifact_registry_host" {
  description = "Docker registry host — set as image.registry in the Helm values."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.ar_repo_name}"
}

output "docker_login_command" {
  description = "Configure docker/CI to push to Artifact Registry."
  value       = "gcloud auth configure-docker ${var.region}-docker.pkg.dev"
}

output "edge_ip" {
  description = "Reserved external IP for the edge LB — point the DuckDNS A-record here."
  value       = google_compute_global_address.edge.address
}

output "edge_ip_name" {
  description = "Name of the reserved IP — set as edge.gatewayAddressName in values-gke.yaml."
  value       = google_compute_global_address.edge.name
}

# --- GitHub Actions Workload Identity Federation ---
# Paste these into the repo's Settings > Secrets and variables > Actions > Variables:
output "ci_gcp_project_id" {
  description = "GitHub repo var GCP_PROJECT_ID"
  value       = var.project_id
}

output "ci_wif_provider" {
  description = "GitHub repo var GCP_WIF_PROVIDER (full provider resource name)"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "ci_deploy_sa" {
  description = "GitHub repo var GCP_DEPLOY_SA (CI service account email)"
  value       = google_service_account.ci.email
}
