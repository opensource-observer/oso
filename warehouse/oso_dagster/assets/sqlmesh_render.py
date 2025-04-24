from datetime import datetime

import dlt
import sqlglot as sql
from dagster import AssetExecutionContext
from dagster_sqlmesh import SQLMeshResource
from dagster_sqlmesh.controller.base import DEFAULT_CONTEXT_FACTORY
from sqlglot import exp

from ..factories import dlt_factory


@dlt.resource(
    primary_key="model_name",
    name="rendered_models",
    write_disposition="merge",
)
def get_rendered_models(
    context: AssetExecutionContext,
    sqlmesh: SQLMeshResource,
    environment: str,
):
    """
    Fetches and renders SQLMesh models.

    Args:
        context (AssetExecutionContext): The asset execution context
        sqlmesh (SQLMeshResource): The SQLMesh resource
        environment (str): The environment to render models for

    Yields:
        Dict: Information about each rendered model
    """
    controller = sqlmesh.get_controller(context_factory=DEFAULT_CONTEXT_FACTORY, log_override=context.log)

    with controller.instance(environment, "model_renderer") as mesh:
        models = mesh.models()
        context.log.info(f"Found {len(models)} models in the SQLMesh context")

        for name, model in models.items():
            try:
                context.log.debug(f"Rendering model: {name}")
                rendered_sql = mesh.context.render(model).sql(
                    dialect="presto",
                    pretty=True,
                    normalize=True,
                )
                expr = sql.parse_one(name)

                if not isinstance(expr, exp.Column) and not isinstance(
                    expr.this, exp.Identifier
                ):
                    raise ValueError(f"Invalid model name: {name}")

                yield {
                    "model_name": expr.this.this,
                    "rendered_sql": rendered_sql,
                    "rendered_at": datetime.now(),
                }

            except Exception as e:
                context.log.error(f"Error rendering model {name}: {str(e)}")


@dlt_factory(
    key_prefix="sqlmesh",
    name="rendered_models",
    compute_kind="sqlmesh",
)
def sqlmesh_render_models(
    context: AssetExecutionContext,
    sqlmesh: SQLMeshResource,
    sqlmesh_infra_config: dict,
):
    """
    Asset factory for rendering SQLMesh models.

    Args:
        context (AssetExecutionContext): The asset execution context
        sqlmesh (SQLMeshResource): The SQLMesh resource
        sqlmesh_infra_config (dict): Configuration for SQLMesh

    Yields:
        Resource: The get_rendered_models resource with rendered models
    """
    environment = sqlmesh_infra_config.get("environment", "dev")

    yield get_rendered_models(
        context=context,
        sqlmesh=sqlmesh,
        environment=environment,
    )
