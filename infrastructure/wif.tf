# Keyless CI auth: GitHub Actions mints an OIDC token, GCP trades it for a
# short-lived SA credential via Workload Identity Federation — no long-lived JSON
# key in GitHub secrets. The build-images.yml workflow uses this (inert until the
# repo vars below are set). Restricted to one repo via the attribute condition.
resource "google_service_account" "ci" {
  account_id   = "${var.cluster_name}-ci"
  display_name = "EasyFocus CI (Artifact Registry push)"
}

# CI pushes images -> needs writer on the registry.
resource "google_artifact_registry_repository_iam_member" "ci_writer" {
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.ci.email}"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.enabled]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  # Only tokens from our repo may impersonate the SA.
  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Let workflows from var.github_repo impersonate the CI service account.
resource "google_service_account_iam_member" "ci_wif" {
  service_account_id = google_service_account.ci.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}
