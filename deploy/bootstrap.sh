#!/usr/bin/env bash
# One-shot bring-up of the EasyFocus stack on ANY kubectl-reachable cluster:
# local kind, a kubeadm/k3s cluster on VMs, or managed (GKE etc).
#
# Auto-detects what the target cluster needs:
#   - creates a kind cluster only if kind is installed and none exists
#   - ensures a default StorageClass (PVCs hang forever without one)
#   - resolves the real CoreDNS ClusterIP (k3s uses 10.43.0.10, not 10.96.0.10)
#
# Run from the repo root:  bash deploy/bootstrap.sh
set -euo pipefail

CLUSTER=easyfocus
HERE="$(cd "$(dirname "$0")" && pwd)"
CHART="$HERE/helm/easyfocus"

# --- 0. sanity: kubectl can reach a cluster ---
if ! kubectl cluster-info > /dev/null 2>&1; then
  if command -v kind > /dev/null 2>&1; then
    echo "==> no reachable cluster — creating kind cluster '$CLUSTER'"
    kind create cluster --config "$HERE/kind/cluster.yaml"
  else
    echo "ERROR: kubectl cannot reach a cluster and kind is not installed." >&2
    echo "Point your kubeconfig at the target cluster, or install kind." >&2
    exit 1
  fi
elif command -v kind > /dev/null 2>&1 && ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  # kubectl reaches *something*; if kind exists but our cluster doesn't, the
  # current context is an external cluster — use it as-is, don't create kind.
  echo "==> using existing cluster from current kubectl context"
fi
echo "    context: $(kubectl config current-context)"

# --- 1. default StorageClass (Postgres/Kafka/Chroma PVCs need one) ---
if ! kubectl get storageclass -o jsonpath='{.items[*].metadata.annotations.storageclass\.kubernetes\.io/is-default-class}' 2>/dev/null | grep -q true; then
  echo "==> no default StorageClass — installing local-path-provisioner"
  kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.31/deploy/local-path-storage.yaml
  kubectl patch storageclass local-path \
    -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
else
  echo "==> default StorageClass: $(kubectl get sc -o jsonpath='{range .items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")]}{.metadata.name}{end}')"
fi

# --- 2. resolve CoreDNS ClusterIP (nginx gateway resolver needs the real one) ---
DNS_IP=$(kubectl -n kube-system get svc -l k8s-app=kube-dns \
  -o jsonpath='{.items[0].spec.clusterIP}' 2>/dev/null || echo "")
if [ -z "$DNS_IP" ]; then
  echo "WARN: could not detect CoreDNS ClusterIP, falling back to chart default" >&2
  DNS_ARG=()
else
  echo "==> CoreDNS ClusterIP: $DNS_IP"
  DNS_ARG=(--set clusterDNS="$DNS_IP")
fi

# --- 3. Envoy Gateway edge (portable kind -> GKE; ingress-nginx EOL 2026-03-24) ---
EG_VERSION=v1.8.1
echo "==> Envoy Gateway ${EG_VERSION}"
helm upgrade --install eg oci://docker.io/envoyproxy/gateway-helm \
  --version "$EG_VERSION" -n envoy-gateway-system --create-namespace --wait
kubectl apply -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: eg
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
EOF

# --- 4. image tag: git sha if CI built it, else latest ---
SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
IMAGE_TAG="latest"
if [ -n "$SHA" ]; then
  REGISTRY="ghcr.io/mikitavydrankou"
  if docker manifest inspect "${REGISTRY}/collabathon2025-auth-svc:${SHA}" > /dev/null 2>&1; then
    IMAGE_TAG="$SHA"
  fi
fi

# --- 5. deploy the app ---
echo "==> helm upgrade --install (image tag: $IMAGE_TAG)"
helm upgrade --install easyfocus "$CHART" \
  -f "$CHART/values.yaml" \
  -f "$CHART/values-local.yaml" \
  "${DNS_ARG[@]}" \
  --set image.tag="$IMAGE_TAG" \
  --wait --timeout 10m

# --- 6. access hints ---
LB_IP=$(kubectl -n envoy-gateway-system get svc \
  -l gateway.envoyproxy.io/owning-gateway-name=easyfocus \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
echo
if [ -n "$LB_IP" ]; then
  echo "Done. Edge has a LoadBalancer IP: http://$LB_IP"
  echo "Point easyfocus.local at it in your hosts file, or curl with -H 'Host: easyfocus.local'."
else
  echo "Done. No LoadBalancer IP (kind / bare-metal without MetalLB)."
  echo "Port-forward the Envoy Gateway to localhost:8080:"
  echo "  bash $HERE/local-access.sh"
  echo "Then open http://localhost:8080  (login: alex.brown / password123)"
fi
