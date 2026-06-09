# EasyFocus — Kubernetes deploy

Helm chart that deploys the full EasyFocus stack to a local **kind** cluster
(and later GKE). Mirrors `docker-compose.yml`: 4 HTTP services + nginx gateway +
Next.js frontend + MCP + 3 Kafka workers + migrate/seed Jobs, on Postgres / Kafka
(KRaft) / Redis / Chroma.

## Layout

```
deploy/
  kind/cluster.yaml        kind config (ingress-ready, host :80/:443)
  helm/easyfocus/          umbrella chart
    values.yaml            defaults (image refs, non-secret config)
    values-local.yaml      real secrets — GITIGNORED
    templates/             config, infra, backends, workers, jobs, gateway, frontend, ingress
  bootstrap.sh             kind + ingress-nginx + helm install
```

Images come from `ghcr.io/mikitavydrankou/collabathon2025-*:latest` (public,
built by `.github/workflows/build-images.yml`).

## Run (inside WSL, repo root)

```bash
bash deploy/bootstrap.sh
```

Then add to the Windows hosts file `C:\Windows\System32\drivers\etc\hosts`:

```
127.0.0.1 easyfocus.local
```

Stop `docker compose` first (it grabs the same ports), then open the edge:

```bash
docker compose down
bash deploy/local-access.sh        # port-forwards Envoy -> localhost:8080
```

Open <http://easyfocus.local:8080> — login `alex.brown` / `password123`.
**Single-origin**: one host serves both the UI and the API (the edge routes
`/auth`, `/qa`, `/transactions`, ... to the gateway, everything else to the
frontend). The frontend image is built with `NEXT_PUBLIC_API_URL=""` so its
calls are same-origin relative — no CORS, one cert.

## Notes

- **Secrets**: `values-local.yaml` mirrors `.env` and is gitignored. The chart's
  `values.yaml` ships placeholders only.
- **Ordering**: `migrate` and `seed` are plain Jobs gated on Postgres TCP via
  initContainers; `helm --wait` blocks until they finish. Backend pods crashloop
  until the schema exists, then recover.
- **Gateway DNS**: the k8s nginx config resolves upstreams through CoreDNS
  (`clusterDNS`, default `10.96.0.10`) instead of the compose-era Docker DNS.
- **Frontend API URL is build-time**: Next.js bakes `NEXT_PUBLIC_*` into the
  client bundle at build, so the runtime env in k8s is ignored. The Dockerfile
  takes `--build-arg NEXT_PUBLIC_API_URL` (CI passes `""` = same-origin). The
  ghcr image only picks this up after a CI run on the updated Dockerfile.
- **Local access**: kind has no cloud LB, so the Envoy Gateway Service stays
  `<pending>` and the Gateway shows `PROGRAMMED=False` (cosmetic — routing
  works; verified in-cluster). `local-access.sh` port-forwards the Envoy proxy.
  For a port-forward-free setup, run
  [cloud-provider-kind](https://github.com/kubernetes-sigs/cloud-provider-kind)
  to assign the LB a real IP (exactly what GKE does natively). In-cluster check:

  ```bash
  EIP=$(kubectl -n envoy-gateway-system get svc -l gateway.envoyproxy.io/owning-gateway-name=easyfocus -o jsonpath='{.items[0].spec.clusterIP}')
  kubectl exec deploy/auth-svc -- python -c "import http.client;c=http.client.HTTPConnection('$EIP',80);c.request('GET','/status/auth',headers={'Host':'easyfocus.local'});print(c.getresponse().read())"
  ```

- **Teardown**: `kind delete cluster --name easyfocus`.

## Next

GitOps via Argo CD — the Jobs already carry `argocd.argoproj.io/sync-wave`
annotations; infra waves + an `Application` manifest come with that step.
