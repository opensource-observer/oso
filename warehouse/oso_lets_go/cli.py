"""
A catchall for development environment tools related to the python tooling.
"""

import dotenv

dotenv.load_dotenv()

import os
import click

from metrics_tools.lib.local.utils import initialize_local_duckdb, reset_local_duckdb


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


@cli.group()
def metrics():
    pass


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
