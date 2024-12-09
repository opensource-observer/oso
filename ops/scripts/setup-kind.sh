#!/bin/bash
##
# Setup kind local testing cluster
#
# Prerequisites:
# - kind
# - kubectl
# - docker
#
# Usage:
# 
#  ./ops/scripts/setup-kind.sh ${branch_name}
##
default_branch_name=$(git rev-parse --abbrev-ref HEAD)
branch_name=${1:-$default_branch_name}
repo_owner=${2:-"opensource-observer"}
repo_name=${3:-"oso"}


# Variables
GITHUB_API_URL="https://api.github.com"

# Make the API request
response=$(curl -s -o /dev/null -w "%{http_code}" \
    "$GITHUB_API_URL/repos/$repo_owner/$repo_name/branches/$branch_name")

# Check if the branch exists on the repository
if [ "$response" -eq 200 ]; then
    echo "Branch '$branch_name' found on remote. Using this branch for the cluster setup"
elif [ "$response" -eq 404 ]; then
    echo "Branch '$branch_name' does not exist in the repository. Push this branch first"
    exit 1
else
    echo "An error occurred: HTTP status code $response."
    exit 1
fi

# Check if the branch exists on github with curl

# Start kind
echo "Ensure kind cluster is running"
kind create cluster --config ops/clusters/kind/local/cluster.yaml

# Ensure that the kubectl context is set to the kind cluster
kubectl config use-context kind-local-test-cluster

# Wait for the cluster to be ready
echo "Ensure kind cluster is ready"
kubectl wait --for=condition=Ready node --all --timeout=5m

# Install helm chart for the flux operator (this is the chicken instanciation
# for the chicken + egg situation)
helm install flux-operator oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator \
  --namespace flux-system \
  --create-namespace

# Generate the flux instance object and apply it to the cluster
cat <<EOF | kubectl apply -f -
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
    - notification-controller
  cluster:
    type: kubernetes
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
  sync:
    kind: GitRepository
    url: "https://github.com/${repo_owner}/${repo_name}.git"
    ref: "refs/heads/${branch_name}"
    path: "./ops/clusters/local"
EOF

echo "The flux instance should now be syncing the repository if everything is going as planned. Check k9s for details"