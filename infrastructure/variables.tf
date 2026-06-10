variable "project_id" {
  type        = string
  description = "GCP project ID that owns the cluster, registry and network."
}

variable "region" {
  type        = string
  description = "Region for the GKE Autopilot cluster and Artifact Registry."
  default     = "europe-central2" # Warsaw — closest to the PL/EU target market
}

variable "cluster_name" {
  type        = string
  description = "Name of the GKE Autopilot cluster."
  default     = "easyfocus"
}

variable "ar_repo_name" {
  type        = string
  description = "Artifact Registry Docker repository that holds the service images."
  default     = "easyfocus"
}

variable "github_repo" {
  type        = string
  description = "GitHub repo (owner/name) allowed to push images via Workload Identity Federation."
  default     = "mikitavydrankou/Collabathon2025"
}

variable "gateway_api_channel" {
  type        = string
  description = "Gateway API CRD channel to install on the cluster (STANDARD or CHANNEL_DISABLED)."
  default     = "CHANNEL_STANDARD"
}
