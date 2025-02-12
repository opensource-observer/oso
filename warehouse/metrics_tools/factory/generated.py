import logging
import typing as t
from datetime import datetime

import pandas as pd
from metrics_tools.compute.client import Client
from metrics_tools.compute.types import ExportType
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.factory.constants import METRICS_COLUMNS_BY_ENTITY
from metrics_tools.runner import MetricsRunner
from metrics_tools.transformer import SQLTransformer
from metrics_tools.transformer.tables import ExecutionContextTableTransform
from metrics_tools.utils import env
from metrics_tools.utils.tables import create_dependent_tables_map
from sqlglot import exp
from sqlmesh import ExecutionContext
from sqlmesh.core.test.context import TestExecutionContext

logger = logging.getLogger(__name__)


def generated_rolling_query(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    ref: PeerMetricDependencyRef,
    vars: t.Dict[str, t.Any],
    rendered_query_str: str,
    table_name: str,
    gateway: str | None,
    *_ignored,
):
    """Generates a rolling query for the given metrics query

    If SQLMESH_MCS_ENABLED is set to true, the query will be sent to the metrics
    calculation service. Otherwise, the query will be executed as a rolling
    query using dataframes (this can be very slow on remote data sources of
    non-trivial size).

    This currently takes advantage of a potential hack in sqlmesh. The snapshot
    evaluator nor the scheduler in sqlmesh seem to care what the response is
    from the python model as long as it's either a dataframe OR a sqlglot
    expression. This means we can return a sqlglot expression that takes the
    ExportReference from the metrics calculation service and use it as a table
    in the sqlmesh query.

    If configured correctly, the metrics calculation service will export a trino
    database in production and if testing, it can export a "LOCALFS" export
    which gives you a path to parquet file with random data (that satisfies the
    requested schema).
    """
    # Transform the query for the current context
    transformer = SQLTransformer(transforms=[ExecutionContextTableTransform(context)])
    query = transformer.transform(rendered_query_str)

    if hasattr(context, "snapshots"):
        print("snapshots")
        print(context.snapshots.values())

    if isinstance(context, TestExecutionContext):
        # MCS should not be used in testing
        mcs_enabled = False
    else:
        mcs_enabled = env.ensure_bool("SQLMESH_MCS_ENABLED", False)
    if not mcs_enabled:
        max_row_size = env.ensure_int(
            "SQLMESH_LOCAL_METRICS_MAX_COMMIT_ROW_SIZE", 10000
        )
        runner = MetricsRunner.from_sqlmesh_context(
            context, query, ref, context._variables.copy()
        )
        df = runner.run_rolling(start, end)
        # If the rolling window is empty we need to yield from an empty tuple
        # otherwise sqlmesh fails. See:
        # https://sqlmesh.readthedocs.io/en/latest/concepts/models/python_models/#returning-empty-dataframes
        total = 0
        if df.empty:
            yield from ()
        else:
            count = len(df)
            total += count
            logger.debug(
                f"table={table_name} yielding rows {count} in {max_row_size} row chunks"
            )
            for i in range(0, count, max_row_size):
                yield t.cast(pd.DataFrame, df[i : i + max_row_size])
        logger.debug(f"table={table_name} yielded rows{total}")
    else:
        logger.info("metrics calculation service enabled")

        mcs_url = env.required_str("SQLMESH_MCS_URL")
        mcs_client = Client.from_url(url=mcs_url)

        columns = [
            (col_name, col_type.sql(dialect="duckdb"))
            for col_name, col_type in METRICS_COLUMNS_BY_ENTITY[
                ref["entity_type"]
            ].items()
        ]

        response = mcs_client.calculate_metrics(
            query_str=rendered_query_str,
            start=start,
            end=end,
            dialect="duckdb",
            batch_size=env.ensure_int("SQLMESH_MCS_BATCH_SIZE", 10),
            columns=columns,
            ref=ref,
            slots=ref.get("slots", env.ensure_int("SQLMESH_MCS_DEFAULT_SLOTS", 2)),
            locals=context._variables,
            dependent_tables_map=create_dependent_tables_map(
                context, rendered_query_str
            ),
            job_retries=env.ensure_int("SQLMESH_MCS_JOB_RETRIES", 8),
            cluster_min_size=env.ensure_int("SQLMESH_MCS_CLUSTER_MIN_SIZE", 5),
            cluster_max_size=env.ensure_int("SQLMESH_MCS_CLUSTER_MAX_SIZE", 16),
            execution_time=execution_time,
            do_not_raise_on_failure=True,
        )
        if not response:
            yield from ()
            return

        column_names = list(map(lambda col: col[0], columns))
        engine_dialect = context.engine_adapter.dialect

        if engine_dialect == "duckdb":
            if response.type not in [ExportType.GCS, ExportType.LOCALFS]:
                raise Exception(f"ExportType={response.type} not supported for duckdb")
            # Create a select query from the exported data
            path = response.payload.get("local_path", response.payload.get("gcs_path"))
            select_query = exp.select(*column_names).from_(
                exp.Anonymous(
                    this="read_parquet",
                    expressions=[exp.Literal(this=path, is_string=True)],
                ),
            )
        elif engine_dialect == "trino":
            if response.type not in [ExportType.TRINO]:
                raise Exception(f"ExportType={response.type} not supported for trino")
            select_query = exp.select(*column_names).from_(response.table_fqn())
        else:
            raise Exception(f"Dialect={context.engine_adapter.dialect} not supported")
        yield select_query
