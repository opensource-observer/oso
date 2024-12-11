#!/usr/bin/env xonsh
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
# default_branch_name = $(git rev-parse --abbrev-ref HEAD).strip()
# branch_name = ${1:-default_branch_name}
# repo_owner = ${2:-"opensource-observer"}
# repo_name = ${3:-"oso"}

# # Variables
# GITHUB_API_URL = "https://api.github.com"

# # Make the API request
# response = $(curl -s -o /dev/null -w "%{http_code}" \
#     "$GITHUB_API_URL/repos/$repo_owner/$repo_name/branches/$branch_name").strip()

# # Check if the branch exists on the repository
# if response == "200":
#     print(f"Branch '{branch_name}' found on remote. Using this branch for the cluster setup")
# elif response == "404":
#     print(f"Branch '{branch_name}' does not exist in the repository. Push this branch first")
#     exit 1
# else:
#     print(f"An error occurred: HTTP status code {response}.")
#     exit 1

# # Start kind
# print("Ensure kind cluster is running")
# $(kind create cluster --config ops/kind/cluster.yaml)

# # Ensure that the kubectl context is set to the kind cluster
# $(kubectl config use-context kind-local-test-cluster)

# # Wait for the cluster to be ready
# print("Ensure kind cluster is ready")
# $(kubectl wait --for=condition=Ready node --all --timeout=5m)

# # Install helm chart for the flux operator (this is the chicken instanciation
# # for the chicken + egg situation)
# $(helm install flux-operator oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator \
#   --namespace flux-system \
#   --create-namespace)

# # Generate the flux instance object and apply it to the cluster
# flux_instance = f"""
# apiVersion: fluxcd.controlplane.io/v1
# kind: FluxInstance
# metadata:
#   name: flux
#   namespace: flux-system
# spec:
#   distribution:
#     version: "2.x"
#     registry: "ghcr.io/fluxcd"
#   components:
#     - source-controller
#     - kustomize-controller
#     - helm-controller
#     - notification-controller
#   cluster:
#     type: kubernetes
#     multitenant: false
#     networkPolicy: true
#     domain: "cluster.local"
#   sync:
#     interval: "30s"
#     kind: GitRepository
#     url: "https://github.com/{repo_owner}/{repo_name}.git"
#     ref: "refs/heads/{branch_name}"
#     path: "./ops/clusters/local"
# """

# with open("/tmp/flux_instance.yaml", "w") as f:
#     f.write(flux_instance)

# # $(kubectl apply -f /tmp/flux_instance.yaml)

# # print("The flux instance should now be syncing the repository if everything is going as planned. Check k9s for details")

# def wait_for_flux_sync():
#     x = $(echo "what is this")
#     print(x)

# wait_for_flux_sync()
# print("what is this here")

def call_kubectl():
    kubectl get pods
