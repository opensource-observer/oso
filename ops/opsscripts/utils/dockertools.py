import logging
import subprocess

from docker.errors import NotFound

import docker

logger = logging.getLogger(__name__)


def initialize_docker_client():
    return docker.from_env()


def ensure_registry_and_image_build(
    docker_client: docker.DockerClient,
    registry_name: str,
    registry_port: int,
    docker_context_path: str,
    dockerfile_path: str,
    image_name: str,
    image_tag: str,
    force_image_build: bool = False,
):
    # Check if the registry is running
    registry_container = docker_client.containers.list(
        filters={"name": registry_name}, all=True
    )

    if len(registry_container) == 0:
        logger.info("Local container registry is not running. Starting the registry")
        create_registry_container(docker_client, registry_name, registry_port)

    image_repo = f"localhost:{registry_port}/{image_name}"

    image = docker_client.images.list(name=image_repo)
    if len(image) == 0 or force_image_build:
        logger.info("Build and publish docker image to local registry")
        build_and_push_docker_image(
            docker_client,
            docker_context_path,
            dockerfile_path,
            image_repo,
            image_tag,
        )
    return image_repo


def create_registry_container(
    docker_client: docker.DockerClient,
    reg_name: str,
    reg_port: int,
):
    try:
        registry = docker_client.containers.get(reg_name)
        if registry.status != "running":
            registry.start()
    except NotFound:
        docker_client.containers.run(
            "registry:2",
            detach=True,
            restart_policy={"Name": "always"},
            ports={"5000/tcp": ("127.0.0.1", reg_port)},
            name=reg_name,
            network="bridge",
        )


def configure_registry_for_nodes(
    docker_client: docker.DockerClient,
    reg_name: str,
    reg_port: int,
    cluster_name: str,
):
    registry_dir = f"/etc/containerd/certs.d/localhost:{reg_port}"
    nodes = subprocess.check_output(
        ["kind", "get", "nodes", "-n", cluster_name], text=True
    ).splitlines()

    for node in nodes:
        node_container = docker_client.containers.get(node)
        node_container.exec_run(f"mkdir -p {registry_dir}")
        hosts_toml = f"""[host."http://{reg_name}:5000"]"""
        node_container.exec_run(
            f"bash -c 'echo \"{hosts_toml}\" > {registry_dir}/hosts.toml'"
        )


def connect_registry_to_network(docker_client: docker.DockerClient, reg_name: str):
    registry = docker_client.containers.get(reg_name)
    if "kind" not in registry.attrs["NetworkSettings"]["Networks"]:
        docker_client.networks.get("kind").connect(registry)


def build_and_push_docker_image(
    client: docker.DockerClient,
    build_dir: str,
    dockerfile_path: str,
    image_repo: str,
    image_tag: str,
):
    """This is a hack at best right now to build the local docker container"""
    image, logs = client.images.build(
        path=build_dir,
        dockerfile=dockerfile_path,
        tag=f"{image_repo}:{image_tag}",
    )
    client.images.push(image_repo, tag=image_tag)
