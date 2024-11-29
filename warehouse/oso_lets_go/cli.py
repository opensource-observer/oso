"""
A catchall for development environment tools related to the python tooling.
"""

import typing as t
from pickle import GLOBAL
import dotenv
from metrics_tools.factory.factory import MetricQueryConfig
from oso_lets_go.wizard import MultipleChoiceInput
from sqlglot import pretty

dotenv.load_dotenv()

import os
import click

from metrics_tools.local.utils import initialize_local_duckdb, reset_local_duckdb

CURR_DIR = os.path.dirname(__file__)
METRICS_MESH_DIR = os.path.abspath(os.path.join(CURR_DIR, "../metrics_mesh"))


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.group()
def metrics():
    pass


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


@local.command()
@click.pass_context
def initialize(ctx: click.Context):
    initialize_local_duckdb(ctx.obj["local_duckdb_path"])


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
