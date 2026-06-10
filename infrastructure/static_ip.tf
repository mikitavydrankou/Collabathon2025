# Stable external IP for the L7 load balancer the GKE Gateway provisions.
# Reserving it here (instead of letting the Gateway grab an ephemeral one) means
# the DNS A-record at DuckDNS is set ONCE and never changes across re-applies.
# The Gateway references it by name via spec.addresses (type NamedAddress) —
# see deploy/helm/easyfocus values-gke.yaml `edge.gatewayAddressName`.
#
# Global address: pairs with gatewayClassName gke-l7-global-external-managed.
resource "google_compute_global_address" "edge" {
  name = "${var.cluster_name}-ip"

  depends_on = [google_project_service.enabled]
}
