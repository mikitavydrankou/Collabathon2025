#!/usr/bin/env bash
# One-shot local bring-up: kind cluster + ingress-nginx + EasyFocus Helm release.
# Run inside WSL from the repo root:  bash deploy/bootstrap.sh
set -euo pipefail

CLUSTER=easyfocus
HERE="$(cd "$(dirname "$0")" && pwd)"
CHART="$HERE/helm/easyfocus"

echo "==> kind cluster"
if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config "$HERE/kind/cluster.yaml"
fi

# Gateway API edge. ingress-nginx reached EOL 2026-03-24 (repo read-only, no CVE
# patches) — replaced by Envoy Gateway, which is portable kind -> GKE.
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

IMAGE_TAG=$(git rev-parse HEAD 2>/dev/null || echo "latest")
echo "==> helm upgrade --install (image tag: $IMAGE_TAG)"
helm upgrade --install easyfocus "$CHART" \
  -f "$CHART/values.yaml" \
  -f "$CHART/values-local.yaml" \
  --set image.tag="$IMAGE_TAG" \
  --wait --timeout 10m

echo
echo "Done. Add to your hosts file (Windows: C:\\Windows\\System32\\drivers\\etc\\hosts):"
echo "  127.0.0.1 easyfocus.local api.easyfocus.local"
echo
echo "kind has no cloud LB — port-forward the Envoy Gateway to localhost:80:"
echo "  kubectl -n envoy-gateway-system port-forward \$(kubectl -n envoy-gateway-system get svc -l gateway.envoyproxy.io/owning-gateway-name=easyfocus -o name) 80:80"
echo "Then open http://easyfocus.local  (on GKE the Gateway gets a real external IP instead)"
