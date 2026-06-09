#!/usr/bin/env bash
# Smoke load test: hammer backends from inside the cluster, watch RSS + restarts.
# Proves the resource limits survive light concurrent load (no OOMKill/CrashLoop).
set -u
NS=default

snap_restarts () {
  kubectl get pods -n "$NS" \
    -o 'custom-columns=POD:.metadata.name,RST:.status.containerStatuses[0].restartCount,LASTTERM:.status.containerStatuses[0].lastState.terminated.reason' \
    --no-headers 2>/dev/null | grep -E 'auth-svc|qa-svc|transactions-svc|gateway|kafka|postgres'
}

run_load () {
  target=$1; url=$2
  echo "=== LOAD $target  ($url)  -c 25 -z 30s ==="
  (
    for i in 1 2 3 4 5 6; do
      sleep 5
      pod=$(kubectl get pod -l app="$target" -n "$NS" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
      m=$(kubectl exec "$pod" -n "$NS" -- cat /sys/fs/cgroup/memory.current 2>/dev/null)
      [ -n "$m" ] && echo "   [$((i*5))s] $target RSS = $((m/1048576)) MiB"
    done
  ) &
  sampler=$!
  kubectl run "hey-$target" --rm -i --restart=Never --image=williamyeh/hey -n "$NS" -- \
    -z 30s -c 25 "$url" 2>/dev/null | grep -E 'Requests/sec|Total:|Slowest|Average|\[2|\[4|\[5|status code|Error'
  wait "$sampler"
  echo
}

echo "===== RESTARTS BEFORE ====="
snap_restarts
echo
run_load auth-svc http://auth-svc:8000/health
run_load qa-svc   http://qa-svc:8000/health
echo "===== RESTARTS AFTER (look for jumps / OOMKilled) ====="
snap_restarts
