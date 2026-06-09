#!/usr/bin/env bash
# Sum live RSS (cgroup memory.current) across all running app pods in default ns.
set -u
NS=default
total=0
printf "%-26s %8s\n" "POD" "RSS_MiB"
printf "%-26s %8s\n" "---" "-------"
for pod in $(kubectl get pods -n "$NS" --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}'); do
  m=$(kubectl exec "$pod" -n "$NS" -- cat /sys/fs/cgroup/memory.current 2>/dev/null)
  [ -z "$m" ] && continue
  mib=$((m/1048576))
  total=$((total+mib))
  printf "%-26s %8d\n" "$pod" "$mib"
done
echo "-------------------------------------"
printf "%-26s %8d MiB  (%d.%02d GiB)\n" "TOTAL app+infra" "$total" "$((total/1024))" "$(((total%1024)*100/1024))"
