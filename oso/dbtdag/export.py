# Setup imports
import click
from dbt import flags
from dbt.cli.main import cli, global_flags
from dbt.cli import requires, params as p
from dbt.config.profile import read_user_config
from dbt.tracking import User, active_user
from dbt.task.list import ListTask
from dbt.graph.queue import GraphQueue


# We need to initialize a click command in order to parse the arguments. This
# seems to be the easiest method to get all the necessary arguments used to call
# the things we need to call
#
# WARNING: This is not a very stable set of code it seems. We are getting most
# of these from here (from the list() function in this code)
# https://github.com/dbt-labs/dbt-core/blob/e4fe839e4574187b574473596a471092267a9f2e/core/dbt/cli/main.py
#
@cli.command("export_list_task")
@click.pass_context
@global_flags
@p.exclude
@p.indirect_selection
@p.models
@p.output
@p.output_keys
@p.profile
@p.profiles_dir
@p.project_dir
@p.resource_type
@p.raw_select
@p.selector
@p.state
@p.defer_state
@p.deprecated_state
@p.target
@p.target_path
@p.vars
@requires.postflight
@requires.preflight
@requires.profile
@requires.project
@requires.runtime_config
@requires.manifest
def export_list_task(ctx, **kwargs):
    print(ctx.obj["flags"])
    task = ListTask(ctx.obj["flags"], ctx.obj["runtime_config"], ctx.obj["manifest"])
    return task, True


def call_export_list_task(target, project_dir=None):
    args = ["export_list_task", "--target", target]

    if project_dir:
        args.append("--project-dir")
        args.append(project_dir)

    ctx = cli.make_context(
        cli.name,
        ["export_list_task", "--target", target],
    )

    ctx.obj = {"manifest": None, "callbacks": []}
    results, success = cli.invoke(ctx)
    if not success:
        raise Exception("invocation was not successful")
    return results


def get_graph_queue_scores(target, project_dir=None):
    task = call_export_list_task(target, project_dir)

    task.compile_manifest()
    graph = task.graph.graph

    queue = GraphQueue(graph, task.manifest, ())
    return queue._get_scores(graph)
