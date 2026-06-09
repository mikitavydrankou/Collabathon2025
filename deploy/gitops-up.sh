#!/usr/bin/env bash
# GitOps bring-up: take a fresh (or empty) cluster to the full EasyFocus stack
# the *GitOps* way — Argo CD owns the app + monitoring, this script only lays the
# pieces Argo can't bootstrap itself (cluster, LB, gateway CRDs, Argo itself, and
# the out-of-band Secrets that must never live in git).
#
#   bash deploy/gitops-up.sh
#
# Idempotent: re-run any time, it converges. Runs inside WSL (docker/kind/kubectl/
# helm live there).
#
# Secrets (never committed):
#   - easyfocus-secret  — rendered from the gitignored values-local.yaml
#   - alertmanager-telegram — from $TELEGRAM_BOT_TOKEN (export before running;
#     skipped with a warning if unset, alerts just won't reach Telegram)
set -euo pipefail

CLUSTER=easyfocus
HERE="$(cd "$(dirname "$0")" && pwd)"
CHART="$HERE/helm/easyfocus"

METALLB_VERSION=v0.14.9
ARGOCD_VERSION=v3.4.3
EG_VERSION=v1.8.1

# --- 0. cluster reachable, else create kind ---
if ! kubectl cluster-info >/dev/null 2>&1; then
  if command -v kind >/dev/null 2>&1; then
    echo "==> no reachable cluster — creating kind cluster '$CLUSTER'"
    kind create cluster --config "$HERE/kind/cluster.yaml"
  else
    echo "ERROR: kubectl cannot reach a cluster and kind is not installed." >&2
    exit 1
  fi
fi
echo "    context: $(kubectl config current-context)"

# --- 1. default StorageClass (Postgres/Kafka/Chroma PVCs need one) ---
if ! kubectl get storageclass -o jsonpath='{.items[*].metadata.annotations.storageclass\.kubernetes\.io/is-default-class}' 2>/dev/null | grep -q true; then
  echo "==> no default StorageClass — installing local-path-provisioner"
  kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.31/deploy/local-path-storage.yaml
  kubectl patch storageclass local-path \
    -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
else
  echo "==> default StorageClass present"
fi

# --- 2. MetalLB — gives the Envoy Gateway LB Service a real IP on kind, so the
#        Gateway reaches Programmed=True (Argo health-gates on it otherwise).
#        Pool is derived from the kind docker network; deploy/metallb/pool.yaml
#        pins it (172.21.255.200-250). Adjust the pool if your kind net differs:
#        docker network inspect kind -f '{{range .IPAM.Config}}{{.Subnet}} {{end}}'
echo "==> MetalLB ${METALLB_VERSION}"
kubectl apply -f "https://raw.githubusercontent.com/metallb/metallb/${METALLB_VERSION}/config/manifests/metallb-native.yaml"
kubectl -n metallb-system rollout status deploy/controller --timeout=120s
kubectl -n metallb-system wait --for=condition=Available deploy/controller --timeout=120s
# webhook needs a moment past Available before it accepts the pool CRs
until kubectl apply -f "$HERE/metallb/pool.yaml" 2>/dev/null; do
  echo "    waiting for MetalLB webhook..."; sleep 3
done

# --- 3. Envoy Gateway edge (provides the Gateway/HTTPRoute CRDs + controller) ---
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

# --- 4. Argo CD ---
echo "==> Argo CD ${ARGOCD_VERSION}"
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"
kubectl -n argocd rollout status deploy/argocd-server --timeout=300s

# --- 5. out-of-band Secrets (NOT managed by Argo — see createSecret=false) ---
# easyfocus-secret: render the chart's Secret from the gitignored values-local.yaml.
if [ ! -f "$CHART/values-local.yaml" ]; then
  echo "ERROR: $CHART/values-local.yaml missing — it holds the real DB/JWT/OpenAI creds." >&2
  echo "       Copy it from your .env (see deploy/README.md) before running." >&2
  exit 1
fi
echo "==> easyfocus-secret (from values-local.yaml)"
helm template easyfocus "$CHART" \
  -f "$CHART/values.yaml" -f "$CHART/values-local.yaml" \
  --set createSecret=true -s templates/config.yaml \
  | kubectl apply -n default -f -

# alertmanager-telegram: bot token from env, into the monitoring ns (created here
# so the secret exists before the kube-prometheus-stack app's Alertmanager starts).
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "==> alertmanager-telegram secret"
  kubectl -n monitoring create secret generic alertmanager-telegram \
    --from-literal=token="$TELEGRAM_BOT_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -
else
  echo "WARN: TELEGRAM_BOT_TOKEN unset — skipping alertmanager-telegram secret." >&2
  echo "      Alertmanager will not start until it exists; export the token and re-run." >&2
fi

# --- 6. Argo Applications (app + monitoring stack, synced from git) ---
echo "==> applying Argo Applications"
kubectl apply -f "$HERE/argo/"

# --- 7. wait + access hints ---
echo "==> waiting for apps to sync (Argo polls git ~every 3m on first run)"
for app in kube-prometheus-stack loki promtail tempo easyfocus; do
  echo "  - $app"
  kubectl -n argocd wait --for=jsonpath='{.status.health.status}'=Healthy \
    "application/$app" --timeout=600s || echo "    (still progressing — check Argo UI)"
done

LB_IP=$(kubectl -n envoy-gateway-system get svc \
  -l gateway.envoyproxy.io/owning-gateway-name=easyfocus \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
echo
echo "Done."
[ -n "$LB_IP" ] && echo "  App edge: http://$LB_IP   (Host: easyfocus.local)"
echo "  Argo CD / Grafana / Prometheus: bash deploy/cluster.sh pf && bash deploy/cluster.sh creds"
