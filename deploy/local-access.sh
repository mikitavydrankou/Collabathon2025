#!/usr/bin/env bash
# Single-origin local access to the kind/k8s stack. The frontend bundle is built
# with NEXT_PUBLIC_API_URL="" (relative URLs), so UI and API are reached through
# the SAME origin = the Envoy Gateway edge. The edge accepts Host `localhost`, so
# NO hosts-file edit is needed.
#
# Run this (inside WSL), then open  http://localhost:8080  in a Windows browser.
#   login: alex.brown / password123
#
# kind's MetalLB IP isn't routable from the WSL host / Windows, so we port-forward
# the Envoy proxy Service (bound to 0.0.0.0 so the Windows host can reach it via
# localhost). On GKE the Gateway gets a real external IP and no port-forward is
# needed.
set -euo pipefail

NS=envoy-gateway-system
PORT="${1:-8080}"

SVC=$(kubectl -n "$NS" get svc \
  -l gateway.envoyproxy.io/owning-gateway-name=easyfocus \
  -o jsonpath='{.items[0].metadata.name}')
if [ -z "$SVC" ]; then
  echo "Envoy gateway service not found — is the chart installed?" >&2
  exit 1
fi

echo "edge -> http://localhost:${PORT}   (UI + API, single origin)"
echo "login: alex.brown / password123"
echo "Ctrl-C to stop."
kubectl -n "$NS" port-forward --address 0.0.0.0 "svc/$SVC" "${PORT}:80"
