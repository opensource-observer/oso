import subprocess
import sys

import click
import requests

flux_instance_yaml = """
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
  interval: "30s"
  kind: GitRepository
  url: "https://github.com/{repo_owner}/{repo_name}.git"
  ref: "refs/heads/{branch_name}"
  path: "./ops/clusters/local"
"""


@click.command()
@click.argument("branch_name", required=False)
@click.argument("repo_owner", default="opensource-observer")
@click.argument("repo_name", default="oso")
def main(branch_name, repo_owner, repo_name):
    if not branch_name:
        branch_name = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode("utf-8")
        )

    github_api_url = "https://api.github.com"
    response = requests.get(
        f"{github_api_url}/repos/{repo_owner}/{repo_name}/branches/{branch_name}"
    )

    if response.status_code == 200:
        click.echo(
            f"Branch '{branch_name}' found on remote. Using this branch for the cluster setup"
        )
    elif response.status_code == 404:
        click.echo(
            f"Branch '{branch_name}' does not exist in the repository. Push this branch first"
        )
        sys.exit(1)
    else:
        click.echo(f"An error occurred: HTTP status code {response.status_code}.")
        sys.exit(1)

    click.echo("Ensure kind cluster is running")
    subprocess.run(
        ["kind", "create", "cluster", "--config", "ops/kind/cluster.yaml"], check=True
    )

    subprocess.run(
        ["kubectl", "config", "use-context", "kind-local-test-cluster"], check=True
    )

    click.echo("Ensure kind cluster is ready")
    subprocess.run(
        ["kubectl", "wait", "--for=condition=Ready", "node", "--all", "--timeout=5m"],
        check=True,
    )

    subprocess.run(
        [
            "helm",
            "install",
            "flux-operator",
            "oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator",
            "--namespace",
            "flux-system",
            "--create-namespace",
        ],
        check=True,
    )

    subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=flux_instance_yaml.encode("utf-8"),
        check=True,
    )

    click.echo(
        "The flux instance should now be syncing the repository if everything is going as planned. Check k9s for details"
    )


if __name__ == "__main__":
    main()
