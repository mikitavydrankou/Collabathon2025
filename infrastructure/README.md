# infrastructure/ — Terraform for GKE

Provisions the managed-cloud side of EasyFocus on GCP. Everything here is IaC —
no clicking in the console.

## What it creates

| Resource | File | Notes |
|----------|------|-------|
| Enabled APIs | `apis.tf` | compute, container, artifactregistry |
| VPC + subnet + Cloud NAT | `network.tf` | VPC-native, private nodes, outbound via NAT |
| GKE Autopilot cluster | `gke.tf` | per-Pod billing, Gateway API enabled, private nodes |
| Artifact Registry (Docker) | `artifact_registry.tf` | one repo for all service images + node pull IAM |
| Reserved external IP | `static_ip.tf` | stable edge IP for the DuckDNS A-record |
| GitHub WIF (keyless CI) | `wif.tf` | OIDC pool + CI service account, no JSON key |

The app itself (Helm chart + Argo + monitoring) is **not** here — that lives in
`../deploy/` and is applied to the cluster after it exists (GitOps via Argo CD).
HTTPS extras (cert-manager + Let's Encrypt) live in `../deploy/gke/`.

## Prerequisites

- A GCP project (free `$300` credits work). `gcloud` CLI authed: `gcloud auth login && gcloud auth application-default login`.
- Terraform >= 1.7.

## Usage

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars   # set project_id

terraform init
terraform plan
terraform apply
# or the wrapper (init + apply + prints next steps):
#   bash apply.sh
#   USE_GCS_BACKEND=1 bash apply.sh   # also create the remote-state bucket
```

Then wire kubectl + registry from the outputs:

```bash
terraform output -raw get_credentials_command | bash   # kubectl context
terraform output -raw docker_login_command   | bash    # local docker push auth
terraform output -raw artifact_registry_host           # -> values-gke.yaml image.registry
terraform output -raw edge_ip                          # -> DuckDNS A-record
```

### Wire CI (keyless image push)

After apply, set three **repo variables** (Settings → Secrets and variables →
Actions → *Variables*) from the outputs — then `build-images.yml` mirrors images
to Artifact Registry on every push, no JSON key:

```bash
terraform output -raw ci_gcp_project_id   # -> GCP_PROJECT_ID
terraform output -raw ci_wif_provider     # -> GCP_WIF_PROVIDER
terraform output -raw ci_deploy_sa        # -> GCP_DEPLOY_SA
```

(Optional vars: `GCP_REGION`, `AR_REPO` — default to `europe-central2` / `easyfocus`.)

### Bring the app up (GitOps, same as kind)

```bash
# 1. Edit deploy/helm/easyfocus/values-gke.yaml: image.registry (AR host) + host (DuckDNS).
# 2. Deploy with the GKE overlay, then HTTPS — see ../deploy/gke/README.md.
bash ../deploy/gitops-up.sh
```

> Cutover vs kind, all pre-wired in `values-gke.yaml`: `image.registry` → AR host,
> `gatewayClassName` `eg` → `gke-l7-global-external-managed`, plain HTTP → HTTPS
> (cert-manager). DNS A-record → `edge_ip`.

## Teardown (stop the credit burn)

```bash
terraform destroy
```

`deletion_protection = false` on the cluster makes this work without a console
trip. APIs stay enabled (`disable_on_destroy = false`).

## State

State is local by default. For anything beyond a solo demo, uncomment the `gcs`
backend in `versions.tf` and create the bucket first (command in that file).
