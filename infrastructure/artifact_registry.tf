# One Docker repo holds every service image (auth/transactions/chatbot/qa/mcp/
# workers/outbox-relay/frontend). Images push as
#   <region>-docker.pkg.dev/<project>/<repo>/<image>:<tag>
# CI builds and pushes here; the Helm chart's image.registry points at it.
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = var.ar_repo_name
  format        = "DOCKER"
  description   = "EasyFocus service images"

  depends_on = [google_project_service.enabled]
}

# Let the cluster's Autopilot nodes pull from the repo. Autopilot nodes run as
# the default compute service account; grant it read on the registry.
data "google_project" "this" {}

resource "google_artifact_registry_repository_iam_member" "node_pull" {
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${data.google_project.this.number}-compute@developer.gserviceaccount.com"
}
