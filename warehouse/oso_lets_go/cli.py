"""
A catchall for development environment tools related to the python tooling.
"""

import asyncio
import getpass
import logging
import subprocess
import sys
import typing as t
import warnings
from contextlib import contextmanager
from datetime import datetime, timedelta

import aiotrino
import dotenv
import git
import kr8s
from kr8s.objects import Job, Namespace, Service
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.factory.constants import METRICS_COLUMNS_BY_ENTITY
from metrics_tools.factory.factory import MetricQueryConfig, timeseries_metrics
from metrics_tools.local.loader import LocalTrinoDestinationLoader
from metrics_tools.local.manager import LocalWarehouseManager
from metrics_tools.transfer.gcs import GCSTimeOrderedStorage
from metrics_tools.transfer.trino import TrinoExporter
from metrics_tools.utils.logging import setup_module_logging
from metrics_tools.utils.tables import list_query_table_dependencies
from metrics_tools.utils.testing import load_timeseries_metrics
from numpy import std
from opsscripts.cli import cluster_setup
from opsscripts.utils.dockertools import (
    build_and_push_docker_image,
    initialize_docker_client,
)
from opsscripts.utils.k8stools import deploy_oso_k8s_job
from oso_lets_go.wizard import MultipleChoiceInput
from sqlglot import pretty
from sqlmesh.core.dialect import parse_one
from traitlets import default

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

import os

import click
from metrics_tools.local.config import Config as LocalManagerConfig
from metrics_tools.local.config import (
    DuckDbLoaderConfig,
    LoaderConfig,
    LocalTrinoLoaderConfig,
)
from metrics_tools.local.utils import TABLE_MAPPING

CURR_DIR = os.path.dirname(__file__)
METRICS_MESH_DIR = os.path.abspath(os.path.join(CURR_DIR, "../metrics_mesh"))
REPO_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../"))
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "opensource-observer")


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    setup_module_logging("oso_lets_go", color=True)
    setup_module_logging("metrics_tools", color=True)
    setup_module_logging("oso_dagster", color=True)
    setup_module_logging("opsscripts", color=True)
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.group()
@click.pass_context
def metrics(ctx: click.Context):
    ctx.obj["used_metrics_sub_command"] = True


@cli.group()
def ops():
    pass


ops.command()(cluster_setup)


def find_or_choose_metric(metric: str):
    timeseries_metrics = load_timeseries_metrics(METRICS_MESH_DIR)

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
    return matches[choice]


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
    chosen_metric = find_or_choose_metric(metric)
    assert chosen_metric, f"Could not find metric {metric}"
    print(chosen_metric["rendered_query"].sql(pretty=True, dialect=dialect))


@click.group()
@click.pass_context
def local(ctx: click.Context):
    if ctx.obj.get("used_metrics_sub_command", False):
        warnings.warn(
            "The `metrics` subcommand is no longer used with `local`. Please use `oso local` directly"
        )

    local_duckdb_path = os.getenv("SQLMESH_DUCKDB_LOCAL_PATH")
    if not local_duckdb_path:
        raise Exception("You need to add SQLMESH_DUCKDB_LOCAL_PATH to your .env")

    ctx.obj["local_duckdb_path"] = local_duckdb_path

    local_trino_duckdb_path = os.getenv("SQLMESH_DUCKDB_LOCAL_TRINO_PATH", None)
    # If we don't set the local trino path then we add a trino suffix to the filename.
    if not local_trino_duckdb_path:
        local_duckdb_dirname = os.path.dirname(local_duckdb_path)
        local_duckdb_filename = os.path.basename(local_duckdb_path)
        name, extension = os.path.splitext(local_duckdb_filename)
        local_trino_duckdb_filename = f"{name}-trino{extension}"
        local_trino_duckdb_path = os.path.join(
            local_duckdb_dirname, local_trino_duckdb_filename
        )
        logger.info(
            f"SQLMESH_DUCKDB_LOCAL_TRINO_PATH not set. Using {local_trino_duckdb_path} for local trino state"
        )
    ctx.obj["local_trino_duckdb_path"] = local_trino_duckdb_path


cli.add_command(local)
metrics.add_command(local)


@local.command()
@click.pass_context
@click.option(
    "-m",
    "--max-results-per-query",
    default=1000,
    help="The max results for local data downloads. Use if there's limited space on your device. Set to zero for all results",
)
@click.option(
    "-d",
    "--max-days",
    default=3,
    help="The max number of days of data to download from timeseries row restricted data",
)
@click.option("--local-trino/--no-local-trino", default=False)
def initialize(
    ctx: click.Context, max_results_per_query: int, max_days: int, local_trino: bool
):
    loader = LoaderConfig(
        type="duckdb",
        config=DuckDbLoaderConfig(duckdb_path=ctx.obj["local_duckdb_path"]),
    )

    if local_trino:
        loader = LoaderConfig(
            type="local-trino",
            config=LocalTrinoLoaderConfig(
                duckdb_path=ctx.obj["local_trino_duckdb_path"]
            ),
        )

    local_manager_config = LocalManagerConfig(
        repo_dir=REPO_DIR,
        table_mapping=TABLE_MAPPING,
        max_days=max_days,
        max_results_per_query=max_results_per_query,
        project_id=PROJECT_ID,
        loader=loader,
    )

    manager = LocalWarehouseManager.from_config(local_manager_config)

    manager.initialize()


@cli.group()
def production():
    pass


@production.command()
@click.option("--hive-catalog", default="source")
@click.option("--hive-schema", default="export")
@click.option("--bucket-name", default="oso-dataset-transfer-bucket")
@click.option("--storage-prefix", default="trino-export")
@click.option("--trino-host", required=True)
@click.option("--trino-port", default=8080)
@click.option("--trino-user", default="oso-cli")
@click.option(
    "--expiration", default=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
)
@click.option(
    "--dry-run/--no-dry-run", default=False, help="Run the cleanup without deleting"
)
def clean_expired_trino_hive_files(
    hive_catalog: str,
    hive_schema: str,
    bucket_name: str,
    storage_prefix: str,
    trino_host: str,
    trino_port: int,
    trino_user: str,
    expiration: str,
    dry_run: bool,
):
    asyncio.run(
        run_cleanup(
            hive_catalog,
            hive_schema,
            bucket_name,
            storage_prefix,
            trino_host,
            trino_port,
            trino_user,
            expiration,
            dry_run,
        )
    )


@production.command()
@click.option("--namespace", default="production-dagster")
@click.option("--service-account", default="production-dagster")
@click.option("--user-email", default=f"{getpass.getuser()}@opensource.observer")
@click.option("--gateway", default="trino")
def sqlmesh_migrate(
    namespace: str, service_account: str, user_email: str, gateway: str
):
    env_vars = {
        "SQLMESH_POSTGRES_INSTANCE_CONNECTION_STRING": "gcp:secretmanager:production-dagster-sqlmesh-postgres-instance-connection-string/versions/latest",
        "SQLMESH_POSTGRES_USER": "gcp:secretmanager:production-dagster-sqlmesh-postgres-user/versions/latest",
        "SQLMESH_POSTGRES_PASSWORD": "gcp:secretmanager:production-dagster-sqlmesh-postgres-password/versions/latest",
        "SQLMESH_POSTGRES_DB": "sqlmesh-trino",
        "SQLMESH_TRINO_HOST": "production-trino-trino.production-trino.svc.cluster.local",
        "SQLMESH_TRINO_CONCURRENT_TASKS": "64",
        "SQLMESH_MCS_ENABLED": "1",
        "SQLMESH_MCS_URL": "http://production-mcs.production-mcs.svc.cluster.local:8000",
        "SQLMESH_MCS_DEFAULT_SLOTS": "8",
    }
    asyncio.run(
        deploy_oso_k8s_job(
            job_name=f"sqlmesh-migrate-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            namespace=namespace,
            cmd=["sqlmesh", "--gateway", gateway, "migrate"],
            working_dir="/usr/src/app/warehouse/metrics_mesh",
            user_email=user_email,
            env=env_vars,
            resources={
                "requests": {"cpu": "200m", "memory": "1Gi"},
                "limits": {"memory": "1532Mi"},
            },
            extra_pod_spec={
                "serviceAccountName": service_account,
                "nodeSelector": {
                    "pool_type": "standard",
                },
                "tolerations": [
                    {
                        "key": "pool_type",
                        "operator": "Equal",
                        "value": "standard",
                        "effect": "NoSchedule",
                    }
                ],
            },
        )
    )


@production.command()
@click.argument("metric-name")
@click.option("--start", type=click.DateTime(), required=True)
@click.option("--end", type=click.DateTime(), required=True)
@click.option("--execution-time", type=click.DateTime(), default=datetime.now())
@click.option("--mcs-url", default="")
@click.option("--mcs-batch-size", default=10)
@click.option("--use-port-forward/--no-use-port-forward", default=False)
@click.option("--mcs-k8s-service-name", default="production-mcs")
@click.option("--mcs-k8s-deployment-name", default="production-mcs")
@click.option("--mcs-k8s-namespace", default="production-mcs")
@click.option("--mcs-default-slots", default=8)
@click.option("--trino-url", default="")
@click.option("--trino-k8s-service-name", default="production-trino-trino")
@click.option("--trino-k8s-namespace", default="production-trino")
@click.option(
    "--trino-k8s-coordinator-deployment-name",
    default="production-trino-trino-coordinator",
)
@click.option(
    "--trino-k8s-worker-deployment-name", default="production-trino-trino-worker"
)
@click.option("--job-retries", default=5, help="The number of times to retry the job")
@click.option("--cluster-min-size", default=3, help="The minimum cluster size")
@click.option("--cluster-max-size", default=15, help="The maximum cluster size")
def call_mcs(
    metric_name: str,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    mcs_url: str,
    mcs_batch_size: int,
    use_port_forward: bool,
    mcs_k8s_service_name: str,
    mcs_k8s_deployment_name: str,
    mcs_k8s_namespace: str,
    mcs_default_slots: int,
    trino_url: str,
    trino_k8s_service_name: str,
    trino_k8s_namespace: str,
    trino_k8s_coordinator_deployment_name: str,
    trino_k8s_worker_deployment_name: str,
    job_retries: int,
    cluster_min_size: int,
    cluster_max_size: int,
):
    """Used to call the mcs to calculate an already defined metric"""

    @contextmanager
    def get_mcs_url(
        mcs_url: str,
        mcs_k8s_service_name: str,
        mcs_k8s_namespace: str,
        use_port_forward: bool,
    ):
        if not use_port_forward:
            assert mcs_url, "You must provide a mcs url"
            yield mcs_url
        else:
            mcs_service = Service.get(
                mcs_k8s_service_name,
                mcs_k8s_namespace,
            )
            with mcs_service.portforward(remote_port="8000") as local_port:
                yield f"http://localhost:{local_port}"

    @contextmanager
    def get_trino_url(
        trino_url: str,
        trino_k8s_service_name: str,
        trino_k8s_namespace: str,
        trino_k8s_coordinator_deployment_name: str,
        trino_k8s_worker_deployment_name: str,
        use_port_forward: bool,
    ):
        if not use_port_forward:
            assert trino_url, "You must provide a trino url"
            yield trino_url
        else:
            coordinator_service = Service.get(
                trino_k8s_service_name,
                trino_k8s_namespace,
            )
            with coordinator_service.portforward(remote_port="8080") as local_port:
                yield f"http://localhost:{local_port}"

    with get_mcs_url(
        mcs_url, mcs_k8s_service_name, mcs_k8s_namespace, use_port_forward
    ) as mcs_url:
        from metrics_tools.compute.client import Client as MCSClient

        if metric_name == "noop":
            # This is a special case for triggering essentially a noop job
            logger.info("Running a noop job")
            rendered_query_str = "SELECT 1 as result"
            columns = [("result", "int")]
            ref = PeerMetricDependencyRef(
                name="noop",
                entity_type="artifact",
                window=1,
                slots=10,
                batch_size=10,
                unit="day",
                cron="@daily",
            )
            variables = {}
            dependencies_dict = {}
        else:
            chosen_metric = find_or_choose_metric(metric_name)
            assert chosen_metric, f"Could not find metric {metric_name}"

            rendered_query = chosen_metric["rendered_query"]
            rendered_query_str = rendered_query.sql(dialect="duckdb")
            # we shouldn't hard code this but it is hardcoded for now
            columns = [
                (col_name, col_type.sql(dialect="duckdb"))
                for col_name, col_type in METRICS_COLUMNS_BY_ENTITY[
                    chosen_metric["ref"]["entity_type"]
                ].items()
            ]

            ref = chosen_metric["ref"]
            variables = chosen_metric["vars"]

            dependencies_set = list_query_table_dependencies(rendered_query, {})
            print(dependencies_set)
            rewrite_map = {
                "metrics.int_events_daily_to_artifact": "metrics.metrics.events_daily_to_artifact",
                "metrics.int_events_daily_to_artifact_with_lag": "metrics.metrics.events_daily_to_artifact_with_lag",
                "metrics.int_issue_event_time_deltas": "metrics.metrics.issue_event_time_deltas",
                "metrics.int_first_of_event_from_artifact": "metrics.metrics.first_of_event_from_artifact",
            }
            dependencies_dict = {
                dep: rewrite_map.get(dep, dep) for dep in dependencies_set
            }
            print(dependencies_dict)

        client = MCSClient.from_url(mcs_url)
        response = client.calculate_metrics(
            query_str=rendered_query_str,
            start=start,
            end=end,
            dialect="duckdb",
            batch_size=mcs_batch_size,
            columns=columns,
            ref=ref,
            slots=ref.get("slots", 8),
            locals=variables,
            dependent_tables_map=dependencies_dict,
            job_retries=job_retries,
            cluster_min_size=cluster_min_size,
            cluster_max_size=cluster_max_size,
            execution_time=execution_time,
        )
        assert response, "No response from MCS"
        print(response)


async def run_cleanup(
    hive_catalog: str,
    hive_schema: str,
    bucket_name: str,
    storage_prefix: str,
    trino_host: str,
    trino_port: int,
    trino_user: str,
    expiration: str,
    dry_run: bool,
):
    from gcloud.aio import storage

    async with storage.Storage() as client:
        gcs_storage = GCSTimeOrderedStorage(
            client=client,
            bucket_name=bucket_name,
            prefix=storage_prefix,
        )
        connection = aiotrino.dbapi.connect(
            host=trino_host,
            port=trino_port,
            user=trino_user,
            catalog=hive_catalog,
        )
        exporter = TrinoExporter(
            hive_catalog,
            hive_schema,
            gcs_storage,
            connection,
            max_concurrency=100,
        )
        await exporter.cleanup_expired(
            datetime.strptime(expiration, "%Y-%m-%d"), dry_run=dry_run
        )


@local.command(
    name="sqlmesh",
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.option("--local-trino/--no-local-trino", default=False)
@click.option("--local-registry-port", default=5001)
@click.option("--redeploy-image/--no-redeploy-image", default=False)
@click.option("--timeseries-start", default="2024-12-01")
@click.option("--repo-dir", default=REPO_DIR)
@click.pass_context
def local_sqlmesh(
    ctx: click.Context,
    local_trino: bool,
    local_registry_port: int,
    redeploy_image: bool,
    timeseries_start: str,
    repo_dir: str,
):
    """Proxy to the sqlmesh command that can be used against a local kind
    deployment or a local duckdb"""

    if local_trino:
        # If git has changes then log a warning
        logger.info("Checking for git changes")
        repo = git.Repo(repo_dir)  # '.' represents the current directory

        if repo.is_dirty():
            logger.warning("You have uncommitted changes. Please commit before running")
            # sys.exit(1)

        # Create an updated local docker image
        client = initialize_docker_client()

        if redeploy_image:
            logger.info("Building local docker image")
            build_and_push_docker_image(
                client,
                repo_dir,
                "docker/images/oso/Dockerfile",
                f"localhost:{local_registry_port}/oso",
                "latest",
            )

        extra_args = ctx.args
        if not ctx.args:
            extra_args = []

        # Open up a port to the trino deployment on the kind cluster
        kr8s_api = kr8s.api(context="kind-oso-local-test-cluster")
        trino_service = Service.get(
            "local-trino-trino",
            "local-trino",
            api=kr8s_api,
        )
        with trino_service.portforward(remote_port="8080") as local_port:
            # TODO Open up a port to the mcs deployment on the kind cluster
            process = subprocess.Popen(
                ["sqlmesh", "--gateway", "local-trino", *extra_args],
                # shell=True,
                cwd=os.path.join(repo_dir, "warehouse/metrics_mesh"),
                env={
                    **os.environ,
                    "SQLMESH_DUCKDB_LOCAL_PATH": ctx.obj["local_trino_duckdb_path"],
                    "SQLMESH_TRINO_HOST": "localhost",
                    "SQLMESH_TRINO_PORT": str(local_port),
                    "SQLMESH_TRINO_CONCURRENT_TASKS": "1",
                    "SQLMESH_MCS_ENABLED": "0",
                    # We set this variable to ensure that we run the minimal
                    # amount of data. By default this ensure that we only
                    # calculate metrics from 2024-12-01. For now this is only
                    # set for trino but must be explicitly set for duckdb
                    "SQLMESH_TIMESERIES_METRICS_START": timeseries_start,
                },
            )
            process.communicate()
    else:
        process = subprocess.Popen(
            ["sqlmesh", *ctx.args],
            cwd=os.path.join(repo_dir, "warehouse/metrics_mesh"),
            env={
                **os.environ,
                "SQLMESH_DUCKDB_LOCAL_PATH": ctx.obj["local_duckdb_path"],
            },
        )
        process.communicate()


@local.command()
@click.pass_context
@click.option(
    "-m",
    "--max-results-per-query",
    default=1000,
    help="The max results for local data downloads. Use if there's limited space on your device. Set to zero for all results",
)
@click.option(
    "-d",
    "--max-days",
    default=3,
    help="The max number of days of data to download from timeseries row restricted data",
)
@click.option("--local-trino/--no-local-trino", default=False)
@click.option("--full-reset/--no-full-reset", default=False)
@click.option("--quiet/--no-quiet", default=False)
def reset(
    ctx: click.Context,
    max_results_per_query: int,
    max_days: int,
    local_trino: bool,
    full_reset: bool,
    quiet: bool,
):
    if not quiet:
        result = click.confirm(
            "This will remove all schemas from the local duckdb except the `sources` schema. Continue?"
        )
        if not result:
            sys.exit(0)

    loader = LoaderConfig(
        type="duckdb",
        config=DuckDbLoaderConfig(duckdb_path=ctx.obj["local_duckdb_path"]),
    )

    if local_trino:
        loader = LoaderConfig(
            type="local-trino",
            config=LocalTrinoLoaderConfig(
                duckdb_path=ctx.obj["local_trino_duckdb_path"]
            ),
        )

    local_manager_config = LocalManagerConfig(
        repo_dir=REPO_DIR,
        table_mapping=TABLE_MAPPING,
        max_days=max_days,
        max_results_per_query=max_results_per_query,
        project_id=PROJECT_ID,
        loader=loader,
    )

    manager = LocalWarehouseManager.from_config(local_manager_config)

    manager.reset(full_reset=full_reset)


@cli.command()
def lets_go():
    pass
