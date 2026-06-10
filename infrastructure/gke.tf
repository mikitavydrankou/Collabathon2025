# GKE Autopilot: Google runs the control plane and right-sizes nodes per Pod
# resource request — no node pools to manage, billed per Pod. Matches the
# capacity sizing (~5 vCPU / 11 Gi) without hand-tuning machine types.
resource "google_container_cluster" "autopilot" {
  name             = var.cluster_name
  location         = var.region
  enable_autopilot = true

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  # Reference the subnet's secondary ranges by name (VPC-native).
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Gateway API (HTTPRoute/Gateway). The app already targets gatewayClassName
  # `eg` on kind; on GKE the gke-l7-* classes ship via this channel so the same
  # HTTPRoutes work against the managed L7 load balancer.
  gateway_api_config {
    channel = var.gateway_api_channel
  }

  # Private nodes (no public IPs); control plane endpoint stays public so you can
  # reach it from your laptop without a bastion. Tighten master_authorized_networks
  # later if this graduates past a demo.
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Autopilot insists on deletion protection by default; off so a demo cluster
  # can be torn down with `terraform destroy` to stop the credit burn.
  deletion_protection = false

  depends_on = [google_project_service.enabled]
}
