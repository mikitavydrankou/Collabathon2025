# EasyFocus — Kubernetes deploy

Helm chart that deploys the full EasyFocus stack to a local **kind** cluster
(and later GKE). Mirrors `docker-compose.yml`: 4 HTTP services + nginx gateway +
Next.js frontend + MCP + 3 Kafka workers + migrate/seed Jobs, on Postgres / Kafka
(KRaft) / Redis / Chroma.

## Layout

```
deploy/
  kind/cluster.yaml        kind config (host :80/:443)
  helm/easyfocus/          umbrella chart
    values.yaml            defaults (image refs, non-secret config)
    values-local.yaml      real secrets — GITIGNORED
    templates/             config, infra, backends, workers, jobs, gateway, frontend, edge
  argo/                    Argo CD Applications (easyfocus app + monitoring stack)
  metallb/pool.yaml        LB IP pool for the kind docker net
  gitops-up.sh             full GitOps bring-up (MetalLB + Envoy GW + Argo CD + apps)
  cluster.sh               kind lifecycle + edge/Argo/Grafana/Prometheus port-forwards
  local-access.sh          standalone port-forward of the Envoy edge -> localhost
```

Images come from `ghcr.io/mikitavydrankou/collabathon2025-*:latest` (public,
built by `.github/workflows/build-images.yml`).

## Run — GitOps (inside WSL, repo root)

Argo CD owns the app + monitoring stack; the script lays the pieces Argo can't
bootstrap itself (cluster, MetalLB, Envoy Gateway CRDs, Argo CD, out-of-band
Secrets). Idempotent — re-run to converge.

```bash
export TELEGRAM_BOT_TOKEN=...        # for alert delivery; omit to skip
bash deploy/gitops-up.sh
```

### Open the app

The MetalLB IP is reachable pod-to-pod inside the cluster but NOT from the WSL
host or Windows (kind + MetalLB L2 doesn't route to the docker host). So from a
Windows browser, port-forward the Envoy edge:

```bash
bash deploy/cluster.sh pf      # edge -> localhost:8081 (+ Argo/Grafana/Prom)
bash deploy/cluster.sh creds   # prints all URLs + logins
# or just the edge:
bash deploy/local-access.sh    # edge -> localhost:8080
```

Open <http://localhost:8081> (or `:8080`) — login `alex.brown` / `password123`.
The edge accepts Host `localhost`, so no hosts-file edit is needed.

**Single-origin**: one host serves both the UI and the API (the edge routes
`/auth`, `/qa`, `/transactions`, ... to the gateway, everything else to the
frontend). The frontend image is built with `NEXT_PUBLIC_API_URL=""` so its
calls are same-origin relative — no CORS, one cert.

## Notes

- **Secrets**: `values-local.yaml` mirrors `.env` and is gitignored. The chart's
  `values.yaml` ships placeholders only.
- **Ordering**: `migrate` and `seed` are Jobs gated on Postgres TCP via
  initContainers, ordered by Argo `sync-wave` (migrate -1, seed +1). Backend
  pods crashloop until the schema exists, then recover.
- **Gateway DNS**: the k8s nginx config resolves upstreams through CoreDNS
  (`clusterDNS`, default `10.96.0.10`) instead of the compose-era Docker DNS.
- **Frontend API URL is build-time**: Next.js bakes `NEXT_PUBLIC_*` into the
  client bundle at build, so the runtime env in k8s is ignored. The Dockerfile
  takes `--build-arg NEXT_PUBLIC_API_URL` (CI passes `""` = same-origin). The
  ghcr image only picks this up after a CI run on the updated Dockerfile.
- **LB**: kind has no cloud LB, so `gitops-up.sh` installs **MetalLB**
  (`deploy/metallb/pool.yaml`) to hand the Envoy Gateway Service an IP from the
  kind docker net. This makes the Gateway reach `PROGRAMMED=True` — required so
  Argo's health gate passes (it blocks the sync otherwise). The IP is only
  routable inside the cluster though; for host/Windows access still port-forward
  (see "Open the app"). On GKE the cloud LB gives a genuinely external IP. If your
  kind docker net isn't `172.21.0.0/16`, adjust the pool range (see the script).

- **Teardown**: `kind delete cluster --name easyfocus`.

## GitOps notes

- **Argo owns**: app (`argo/easyfocus.yaml` → `helm/easyfocus`), `kube-prometheus-stack`,
  `loki`, `promtail`. The Application manifests live in `deploy/argo/` and are
  applied by `gitops-up.sh` (Argo is not self-managing yet — no app-of-apps).
- **Secrets stay out of git**: the app chart gates its Secret behind
  `createSecret` (default `true` for a local `helm template`; the Argo app sets
  it `false`). `gitops-up.sh` creates `easyfocus-secret` by rendering it from the
  gitignored `values-local.yaml`, and `alertmanager-telegram` from
  `$TELEGRAM_BOT_TOKEN`.
- **Known-diff suppression**: `argo/easyfocus.yaml` carries `ignoreDifferences`
  for API-defaulted fields (StatefulSet PVC retention / volumeClaimTemplates,
  HTTPRoute parentRefs/backendRefs group/kind/weight) that would otherwise show
  a permanent OutOfSync.
