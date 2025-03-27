import typing as t
from datetime import datetime

import pandas as pd
import sqlglot as sql
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.factory.generated import generated_rolling_query
from metrics_tools.factory.utils import metric_ref_evaluator_context
from metrics_tools.macros import (
    metrics_end,
    metrics_sample_date,
    metrics_sample_interval_length,
    metrics_start,
)
from oso_sqlmesh.macros.to_unix_timestamp import (
    str_to_unix_timestamp,
    to_unix_timestamp,
)
from sqlglot import exp
from sqlmesh import ExecutionContext
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.macros import MacroEvaluator


def generated_query(
    evaluator: MacroEvaluator,
):
    """Simple generated query executor for metrics queries"""
    rendered_query_str = t.cast(str, evaluator.var("rendered_query_str"))
    ref = t.cast(PeerMetricDependencyRef, evaluator.var("ref"))

    with metric_ref_evaluator_context(
        evaluator,
        ref,
        additional_macros={
            "@METRICS_SAMPLE_DATE": metrics_sample_date,
            "@METRICS_SAMPLE_INTERVAL_LENGTH": metrics_sample_interval_length,
            "@METRICS_START": metrics_start,
            "@METRICS_END": metrics_end,
            "@STR_TO_UNIX_TIMESTAMP": str_to_unix_timestamp,
            "@TO_UNIX_TIMESTAMP": to_unix_timestamp,
        },
    ):
        result = evaluator.transform(parse_one(rendered_query_str))
    return result


def generated_rolling_query_proxy(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs,
) -> t.Iterator[pd.DataFrame | exp.Expression]:
    """This acts as the proxy to the actual function that we'd call for
    the metrics model."""
    ref = t.cast(PeerMetricDependencyRef, context.var("ref"))
    vars = t.cast(t.Dict[str, t.Any], context.var("vars"))
    rendered_query_str = t.cast(str, context.var("rendered_query_str"))
    table_name = t.cast(str, context.var("table_name"))

    yield from generated_rolling_query(
        context,
        start,
        end,
        execution_time,
        ref,
        vars,
        rendered_query_str,
        table_name,
        context.gateway,
        # Change the following variable to force reevaluation. Hack for now.
        "version=v5",
    )


def join_all_of_entity_type(
    evaluator: MacroEvaluator,
):
    # A bit of a hack but we know we have a "metric" column. We want to
    # transform this metric id to also include the event_source as a prefix to
    # that metric id in the joined table

    db = t.cast(str, evaluator.var("db"))
    tables: t.List[str] = t.cast(t.List[str], evaluator.var("tables"))
    columns: t.List[str] = t.cast(t.List[str], evaluator.var("columns"))

    transformed_columns = []
    for column in columns:
        if column == "event_source":
            continue
        if column == "metric":
            transformed_columns.append(
                exp.alias_(
                    exp.Concat(
                        expressions=[
                            exp.to_column("event_source"),
                            exp.Literal(this="_", is_string=True),
                            exp.to_column(column),
                        ],
                        safe=False,
                        coalesce=False,
                    ),
                    alias="metric",
                )
            )
        else:
            transformed_columns.append(column)

    query = exp.select(*transformed_columns).from_(sql.to_table(f"{db}.{tables[0]}"))
    for table in tables[1:]:
        query = query.union(
            exp.select(*transformed_columns).from_(sql.to_table(f"{db}.{table}")),
            distinct=False,
        )
    # Calculate the correct metric_id for all of the entity types
    return query


def map_metadata_to_metric(
    evaluator: MacroEvaluator,
):
    metric = t.cast(str, evaluator.var("metric"))
    metadata = t.cast(t.Dict[str, t.Any], evaluator.var("metadata"))
    sql_source_path = t.cast(str, evaluator.var("sql_source_path", ""))
    rendered_sql = t.cast(t.List[str], evaluator.var("rendered_sql", ""))

    description = metadata["description"]
    display_name = metadata["display_name"]

    return exp.select(
        exp.Literal(this=display_name, is_string=True).as_("display_name"),
        exp.Literal(this=description, is_string=True).as_("description"),
        exp.Literal(this=metric, is_string=True).as_("metric"),
        exp.Literal(this=sql_source_path, is_string=True).as_("sql_source_path"),
        exp.Array(
            expressions=[
                exp.Literal(this=query, is_string=True) for query in rendered_sql
            ]
        ).as_("rendered_sql"),
    )


def aggregate_metadata(
    evaluator: MacroEvaluator,
):
    from functools import reduce

    if evaluator.runtime_stage in ["loading", "creating"]:
        return exp.select(
            exp.Literal(this="...", is_string=True).as_("display_name"),
            exp.Literal(this="...", is_string=True).as_("description"),
            exp.Literal(this="...", is_string=True).as_("metric"),
            exp.Literal(this=exp.Array(this=[]), is_string=False).as_(
                "sql_source_path"
            ),
            exp.Literal(this="...", is_string=True).as_("rendered_sql"),
        )

    model_names = [snap.name for snap in evaluator._snapshots.values()]

    metadata_model_names = [
        name
        for name in model_names
        if (col := parse_one(name))
        and isinstance(col, exp.Column)
        and isinstance(col.this, exp.Identifier)
        and col.this.this.startswith("metrics_metadata_")
    ]

    assert len(metadata_model_names) > 0, "No valid metadata models found"

    def make_select(table: str):
        return exp.select(
            exp.column("display_name"),
            exp.column("description"),
            exp.column("metric"),
            exp.column("sql_source_path"),
            exp.column("rendered_sql"),
        ).from_(sql.to_table(f"{table}"))

    selects = [make_select(model) for model in metadata_model_names]

    unique_metrics = reduce(lambda acc, cur: acc.union(cur), selects)

    return (
        exp.select(
            exp.column("display_name"),
            exp.column("description"),
            exp.column("metric"),
            exp.column("sql_source_path"),
            exp.column("rendered_sql"),
        )
        .from_(unique_metrics.subquery())
        .as_("metadata")
    )
