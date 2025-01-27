"""
A catchall for development environment tools related to the python tooling.
"""

import logging
import subprocess
import sys
import typing as t

import dotenv
import git
from kr8s.objects import Service
from metrics_tools.factory.factory import MetricQueryConfig
from metrics_tools.utils.logging import setup_module_logging
from numpy import std
from opsscripts.cli import cluster_setup
from opsscripts.utils.dockertools import (
    build_and_push_docker_image,
    initialize_docker_client,
)
from oso_lets_go.wizard import MultipleChoiceInput
from sqlglot import pretty

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

import os

import click
from metrics_tools.local.utils import (
    initialize_local_duckdb,
    initialize_local_postgres,
    reset_local_duckdb,
)

CURR_DIR = os.path.dirname(__file__)
METRICS_MESH_DIR = os.path.abspath(os.path.join(CURR_DIR, "../metrics_mesh"))
REPO_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../"))


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    setup_module_logging("oso_lets_go")
    setup_module_logging("metrics_tools")
    setup_module_logging("oso_dagster")
    setup_module_logging("opsscripts")
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.group()
def metrics():
    pass


@cli.group()
def ops():
    pass


ops.command()(cluster_setup)


@metrics.command()
@click.argument("metric")
@click.option(
    "--factory-path",
    default=os.path.join(METRICS_MESH_DIR, "models/metrics_factories.py"),
)
@click.option("--dialect", default="duckdb", help="The dialect to render")
@click.pass_context
def render(ctx: click.Context, metric: str, factory_path: str, dialect: str):
    """Renders a given metric query. Useful for testing

    Usage:

        $ oso metrics render <metrics_name>
    """

    # Select all the available options for the metric
    import importlib.util

    from metrics_tools.utils import testing
    from sqlmesh.core.dialect import parse_one

    testing.ENABLE_TIMESERIES_DEBUG = True

    from metrics_tools.factory.factory import GLOBAL_TIMESERIES_METRICS

    # Run the metrics factory in the sqlmesh project. This uses a single default
    # location for now.
    spec = importlib.util.spec_from_file_location(
        "metrics_mesh.metrics_factories", factory_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    timeseries_metrics = GLOBAL_TIMESERIES_METRICS[factory_path]

    matches: t.Dict[str, MetricQueryConfig] = {}

    for depth, config, deps in timeseries_metrics.generate_ordered_queries():
        if config["ref"]["name"] == metric:
            matches[config["table_name"]] = config
        if config["table_name"] == metric:
            matches[config["table_name"]] = config
            break

    if not len(matches):
        print("No matching metrics")
        return
    if len(matches) > 1:
        choice = MultipleChoiceInput(dict(zip(matches.keys(), matches.keys()))).render()
    else:
        choice = list(matches.keys())[0]
    print(matches[choice]["rendered_query"].sql(pretty=True, dialect=dialect))


@metrics.group()
@click.pass_context
def local(ctx: click.Context):
    local_duckdb_path = os.getenv("SQLMESH_DUCKDB_LOCAL_PATH")
    if not local_duckdb_path:
        raise Exception("You need to add SQLMESH_DUCKDB_LOCAL_PATH to your .env")

    ctx.obj["local_duckdb_path"] = local_duckdb_path

    # By default just use the local duckdb path and add .trino.db to the name
    local_trino_duckdb_path = os.getenv(
        "SQLMESH_DUCKDB_LOCAL_TRINO_PATH", f"{local_duckdb_path}.trino.db"
    )
    if local_trino_duckdb_path:
        ctx.obj["local_trino_duckdb_path"] = local_trino_duckdb_path


@local.command()
@click.pass_context
@click.option(
    "-m",
    "--max-results-per-query",
    default=0,
    help="The max results for local data downloads. Use if there's limited space on your device. Set to zero for all results",
)
@click.option(
    "-d",
    "--max-days",
    default=7,
    help="The max number of days of data to download from timeseries row restricted data",
)
@click.option("--local-trino/--no-local-trino", default=False)
def initialize(
    ctx: click.Context, max_results_per_query: int, max_days: int, local_trino: bool
):
    if not local_trino:
        initialize_local_duckdb(
            ctx.obj["local_duckdb_path"],
            max_results_per_query=max_results_per_query,
            max_days=max_days,
        )
    else:
        postgres_service = Service.get(
            name="trino-psql-postgresql", namespace="local-trino-psql"
        )
        with postgres_service.portforward(remote_port=5432) as local_port:
            logger.debug(f"Proxied postgres to port: {local_port}")

            initialize_local_postgres(
                ctx.obj["local_duckdb_path"],
                max_results_per_query=max_results_per_query,
                max_days=max_days,
                postgres_port=local_port,
            )


@local.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True)
)
@click.option("--local-trino/--no-local-trino", default=False)
@click.option("--local-registry-port", default=5001)
@click.option("--redeploy-image/--no-redeploy-image", default=False)
@click.pass_context
def sqlmesh(
    ctx: click.Context,
    local_trino: bool,
    local_registry_port: int,
    redeploy_image: bool,
):
    """Proxy to the sqlmesh command that can be used against a local kind
    deployment or a local duckdb"""

    if local_trino:
        # If git has changes then log a warning
        logger.info("Checking for git changes")
        repo = git.Repo(".")  # '.' represents the current directory

        if repo.is_dirty():
            logger.warning("You have uncommitted changes. Please commit before running")
            # sys.exit(1)

        # Create an updated local docker image
        client = initialize_docker_client()

        if redeploy_image:
            logger.info("Building local docker image")
            build_and_push_docker_image(
                client,
                REPO_DIR,
                "docker/images/oso/Dockerfile",
                f"localhost:{local_registry_port}/oso",
                "latest",
            )

        extra_args = ctx.args
        if not ctx.args:
            extra_args = []

        # Open up a port to the trino deployment on the kind cluster
        trino_service = Service.get("local-trino-trino", "local-trino")
        with trino_service.portforward(remote_port="8080") as local_port:
            # TODO Open up a port to the mcs deployment on the kind cluster
            process = subprocess.Popen(
                ["sqlmesh", "--gateway", "local-trino", *extra_args],
                # shell=True,
                cwd=os.path.join(REPO_DIR, "warehouse/metrics_mesh"),
                env={
                    **os.environ,
                    "SQLMESH_DUCKDB_LOCAL_PATH": ctx.obj["local_trino_duckdb_path"],
                    "SQLMESH_TRINO_HOST": "localhost",
                    "SQLMESH_TRINO_PORT": str(local_port),
                    "SQLMESH_TRINO_CONCURRENT_TASKS": "1",
                    "SQLMESH_MCS_ENABLED": "0",
                },
            )
            process.communicate()
    else:
        process = subprocess.Popen(
            ["sqlmesh", *ctx.args],
            cwd=os.path.join(REPO_DIR, "warehouse/metrics_mesh"),
            env={
                **os.environ,
                "SQLMESH_DUCKDB_LOCAL_PATH": ctx.obj["local_duckdb_path"],
            },
        )
        process.communicate()


@local.command()
@click.option("-q", "--quiet/--no-quiet", default=False)
@click.pass_context
def reset(ctx: click.Context, quiet: bool):
    if not quiet:
        click.confirm(
            "This will remove all schemas from the local duckdb except the `sources` schema. Continue?"
        )
    reset_local_duckdb(ctx.obj["local_duckdb_path"])


@cli.command()
def lets_go():
    pass
