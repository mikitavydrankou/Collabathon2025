#!/usr/bin/env bash
# One-shot Terraform bring-up for the EasyFocus GKE infra.
#
#   bash infrastructure/apply.sh                 # project_id from terraform.tfvars
#   PROJECT_ID=my-proj bash infrastructure/apply.sh
#   USE_GCS_BACKEND=1 PROJECT_ID=my-proj bash infrastructure/apply.sh   # also make state bucket
#
# Runs init + apply, then prints outputs (cluster creds, registry host, edge IP).
# Idempotent: re-run any time. Pass extra terraform flags after the script name,
# e.g. `bash infrastructure/apply.sh -auto-approve`.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

command -v terraform >/dev/null || { echo "terraform not installed" >&2; exit 1; }
command -v gcloud    >/dev/null || { echo "gcloud not installed" >&2; exit 1; }

# project id: env wins, else read it out of terraform.tfvars.
PROJECT_ID="${PROJECT_ID:-$(grep -E '^[[:space:]]*project_id' terraform.tfvars 2>/dev/null | sed -E 's/.*"([^"]+)".*/\1/' || true)}"
[ -n "$PROJECT_ID" ] || { echo "set PROJECT_ID env or project_id in terraform.tfvars" >&2; exit 1; }
REGION="${REGION:-europe-central2}"

echo "==> project=$PROJECT_ID region=$REGION"
gcloud config set project "$PROJECT_ID" >/dev/null

# Optional: create the remote-state bucket once. After this, uncomment the
# backend "gcs" block in versions.tf and re-run to migrate state into it.
if [ "${USE_GCS_BACKEND:-0}" = "1" ]; then
  BUCKET="easyfocus-tfstate-${PROJECT_ID}"
  if ! gcloud storage buckets describe "gs://$BUCKET" >/dev/null 2>&1; then
    echo "==> creating state bucket gs://$BUCKET"
    gcloud storage buckets create "gs://$BUCKET" \
      --location="$REGION" --uniform-bucket-level-access
    gcloud storage buckets update "gs://$BUCKET" --versioning
  fi
  echo "    state bucket ready: gs://$BUCKET"
  echo "    -> uncomment backend \"gcs\" (bucket=$BUCKET) in versions.tf, then re-run."
fi

terraform init -input=false
terraform apply -input=false "$@"

echo
echo "==> outputs"
terraform output
echo
echo "Next: wire kubectl + DNS:"
echo "  terraform output -raw get_credentials_command | bash"
echo "  terraform output -raw edge_ip          # point DuckDNS A-record here"
echo "  terraform output -raw artifact_registry_host   # set image.registry in values-gke.yaml"
