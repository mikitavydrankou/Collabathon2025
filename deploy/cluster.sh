#!/usr/bin/env bash
# kind cluster lifecycle + port-forwards for the EasyFocus dev cluster.
# Runs inside WSL (where docker/kind/kubectl live).
#
#   ./deploy/cluster.sh up        # start the stopped kind cluster
#   ./deploy/cluster.sh down      # stop it (state persists, frees CPU/RAM)
#   ./deploy/cluster.sh status    # nodes + pods
#   ./deploy/cluster.sh pf        # start Grafana/Prometheus/Argo port-forwards
#   ./deploy/cluster.sh pf-stop   # kill the port-forwards
#   ./deploy/cluster.sh creds     # print UI URLs + credentials
#
# NOTE: this stops/starts the cluster containers — it does NOT delete data.
#       Never use `kind delete cluster` here; that wipes everything.
set -euo pipefail

CLUSTER="${CLUSTER:-easyfocus}"
PF_PIDFILE="/tmp/easyfocus-portforwards.pids"

# All node containers belonging to this kind cluster (1 or many).
nodes() {
  docker ps -a --filter "label=io.x-k8s.kind.cluster=${CLUSTER}" --format '{{.Names}}'
}

require_nodes() {
  if [ -z "$(nodes)" ]; then
    echo "No kind cluster '${CLUSTER}' found. Create it first (deploy/kind/cluster.yaml)." >&2
    exit 1
  fi
}

cmd_up() {
  require_nodes
  echo "Starting cluster '${CLUSTER}'..."
  for n in $(nodes); do docker start "$n" >/dev/null && echo "  started $n"; done
  echo "Waiting for API server / nodes to become Ready (up to 120s)..."
  kubectl wait --for=condition=Ready nodes --all --timeout=120s || {
    echo "Nodes not Ready yet — give it a moment, then: ./deploy/cluster.sh status" >&2; exit 1; }
  echo "Cluster up. Pods will self-recover; check with: ./deploy/cluster.sh status"
}

cmd_down() {
  require_nodes
  cmd_pf_stop || true
  echo "Stopping cluster '${CLUSTER}' (state preserved)..."
  for n in $(nodes); do docker stop "$n" >/dev/null && echo "  stopped $n"; done
  echo "Cluster down."
}

cmd_status() {
  echo "=== node containers ==="
  docker ps -a --filter "label=io.x-k8s.kind.cluster=${CLUSTER}" \
    --format 'table {{.Names}}\t{{.Status}}'
  if kubectl cluster-info >/dev/null 2>&1; then
    echo "=== k8s nodes ==="; kubectl get nodes
    echo "=== pods (non-running) ==="
    kubectl get pods -A | awk 'NR==1 || $4!="Running"'
  else
    echo "(API server not reachable — cluster is down or still starting)"
  fi
}

# Start a port-forward in the background, retrying if it drops; record the PID.
_pf() { # ns svc localport remoteport
  ( while true; do
      kubectl -n "$1" port-forward --address 0.0.0.0 "svc/$2" "$3:$4" >/dev/null 2>&1 || true
      sleep 2
    done ) &
  echo $! >> "$PF_PIDFILE"
}

cmd_pf() {
  cmd_pf_stop || true
  : > "$PF_PIDFILE"
  # Envoy edge svc name carries a per-Gateway hash suffix — resolve it by label.
  EDGE_SVC=$(kubectl -n envoy-gateway-system get svc \
    -l gateway.envoyproxy.io/owning-gateway-name=easyfocus \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
  [ -n "$EDGE_SVC" ] && _pf envoy-gateway-system "$EDGE_SVC" 8081 80
  _pf monitoring kube-prometheus-stack-grafana    3001 80
  _pf monitoring kube-prometheus-stack-prometheus 9090 9090
  _pf argocd     argocd-server                    8080 443
  echo "Port-forwards started (auto-restart on drop):"
  cmd_creds
}

cmd_pf_stop() {
  [ -f "$PF_PIDFILE" ] || { echo "No port-forwards tracked."; return 0; }
  while read -r pid; do [ -n "$pid" ] && kill "$pid" 2>/dev/null || true; done < "$PF_PIDFILE"
  rm -f "$PF_PIDFILE"
  # Also sweep any stray kubectl port-forwards.
  pkill -f "kubectl.*port-forward" 2>/dev/null || true
  echo "Port-forwards stopped."
}

cmd_creds() {
  echo "  App edge   http://localhost:8081    alex.brown / password123  (Host: localhost)"
  echo "  Grafana    http://localhost:3001    admin / admin"
  echo -n "  Argo CD    https://localhost:8080   admin / "
  kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath='{.data.password}' 2>/dev/null | base64 -d 2>/dev/null || echo -n '(secret gone)'
  echo
  echo "  Prometheus http://localhost:9090    (no auth)"
}

case "${1:-}" in
  up)       cmd_up ;;
  down)     cmd_down ;;
  status)   cmd_status ;;
  pf)       cmd_pf ;;
  pf-stop)  cmd_pf_stop ;;
  creds)    cmd_creds ;;
  *) echo "usage: $0 {up|down|status|pf|pf-stop|creds}" >&2; exit 1 ;;
esac
