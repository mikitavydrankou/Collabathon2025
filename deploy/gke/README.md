# deploy/gke/ — GKE-only extras

Pieces that only apply when running on GKE (not kind): HTTPS via cert-manager +
Let's Encrypt. The base app/monitoring still come up the normal GitOps way
(`deploy/gitops-up.sh`); these layer on top.

## Order (after `terraform apply` + kubectl context points at GKE)

1. **DNS** — set the DuckDNS A-record to the reserved IP:
   ```bash
   terraform -chdir=../../infrastructure output -raw edge_ip
   # point easyfocus.duckdns.org -> that IP
   ```
2. **App with the GKE overlay** — bring the stack up so the `easyfocus` Gateway
   exists (cert-manager's HTTP-01 solver attaches an HTTPRoute to it):
   ```bash
   # values-gke.yaml: set image.registry + host first (see that file)
   bash ../gitops-up.sh         # or helm upgrade ... -f values-gke.yaml
   ```
3. **cert-manager**:
   ```bash
   kubectl apply -f cert-manager.yaml          # Argo app; wait until Healthy
   kubectl -n cert-manager rollout status deploy/cert-manager
   ```
4. **Issuers + certificate**:
   ```bash
   kubectl apply -f clusterissuer.yaml
   kubectl apply -f certificate.yaml
   kubectl get certificate easyfocus-tls -w    # READY=True in 1-2 min
   ```
5. Open `https://easyfocus.duckdns.org` — `:80` 301-redirects to `:443`.

## Notes / gotchas

- **Hostname must match in 3 places**: `certificate.yaml` dnsNames,
  `values-gke.yaml` edge.host, and the DuckDNS record. Mismatch = challenge fails.
- **Rate limits**: test with `letsencrypt-staging` (in `certificate.yaml` set
  issuerRef name to `letsencrypt-staging`). Staging cert is untrusted — browser
  warns, expected. Switch to `letsencrypt-prod` and delete the `easyfocus-tls`
  secret to force a real re-issue.
- HTTP-01 needs the DNS record live and the Gateway reachable on `:80` *before*
  applying the Certificate — do steps 1-2 first.
- Gateway API support in cert-manager is behind the `enableGatewayAPI` feature
  flag (set in `cert-manager.yaml`).
