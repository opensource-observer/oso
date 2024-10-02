import inspect
import os
import typing as t

from metrics_tools.lib.factories.definition import (
    GeneratedArtifactConfig,
    MetricQuery,
    TimeseriesMetricsOptions,
    generated_entity,
    join_all_of_entity_type,
    reference_to_str,
)
from metrics_tools.models import GeneratedModel
from sqlglot import exp
from sqlmesh.core.model import ModelKindName
from sqlmesh.utils.date import TimeLike

from .macros import (
    metrics_end,
    metrics_entity_type_col,
    metrics_name,
    metrics_sample_date,
    metrics_start,
    relative_window_sample_date,
    metrics_alias_by_entity_type,
)

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../oso_metrics"))

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]


TIME_AGGREGATION_TO_CRON = {
    "daily": "@daily",
    "monthly": "@monthly",
    "weekly": "@weekly",
}
METRICS_COLUMNS_BY_ENTITY: t.Dict[str, t.Dict[str, exp.DataType]] = {
    "artifact": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="clickhouse"),
        "event_source": exp.DataType.build("String", dialect="clickhouse"),
        "to_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
        "from_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
        "metric": exp.DataType.build("String", dialect="clickhouse"),
        "amount": exp.DataType.build("Float64", dialect="clickhouse"),
    },
    "project": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="clickhouse"),
        "event_source": exp.DataType.build("String", dialect="clickhouse"),
        "to_project_id": exp.DataType.build("String", dialect="clickhouse"),
        "from_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
        "metric": exp.DataType.build("String", dialect="clickhouse"),
        "amount": exp.DataType.build("Float64", dialect="clickhouse"),
    },
    "collection": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="clickhouse"),
        "event_source": exp.DataType.build("String", dialect="clickhouse"),
        "to_collection_id": exp.DataType.build("String", dialect="clickhouse"),
        "from_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
        "metric": exp.DataType.build("String", dialect="clickhouse"),
        "amount": exp.DataType.build("Float64", dialect="clickhouse"),
    },
}


def generate_models_from_query(
    calling_file: str,
    query: MetricQuery,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
    start: TimeLike,
    timeseries_sources: t.List[str],
):
    # Turn the source into a dict so it can be used in the sqlmesh context
    query_def_as_input = query._source.to_input()
    query_reference_name = query.reference_name
    refs = query.provided_dependency_refs

    all_tables: t.Dict[str, t.List[str]] = {
        "artifact": [],
        "project": [],
        "collection": [],
    }

    for ref in refs:
        cron = "@daily"
        time_aggregation = ref.get("time_aggregation")
        window = ref.get("window")
        if time_aggregation:
            cron = TIME_AGGREGATION_TO_CRON[time_aggregation]
        else:
            if not window:
                raise Exception("window or time_aggregation must be set")
            assert query._source.rolling
            cron = query._source.rolling["cron"]

        config = GeneratedArtifactConfig(
            query_reference_name=query_reference_name,
            query_def_as_input=query_def_as_input,
            default_dialect=default_dialect,
            peer_table_map=peer_table_map,
            ref=ref,
            timeseries_sources=timeseries_sources,
        )

        table_name = query.table_name(ref)
        all_tables[ref["entity_type"]].append(table_name)
        columns = METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]
        additional_macros = [
            metrics_entity_type_col,
            metrics_alias_by_entity_type,
            relative_window_sample_date,
            (metrics_name, ["metric_name"]),
            metrics_sample_date,
            metrics_end,
            metrics_start,
        ]

        kind_common = {"batch_size": 1, "batch_concurrency": 1}

        # Due to how the schedulers work for sqlmesh we actually can't batch if
        # we're using a weekly cron for a time aggregation. In order to have
        # this work we just adjust the start/end time for the
        # metrics_start/metrics_end and also give a large enough batch time to
        # fit a few weeks. This ensures there's on missing data
        if time_aggregation == "weekly":
            kind_common = {"batch_size": 21, "lookback": 7, "batch_concurrency": 1}
        if time_aggregation == "monthly":
            kind_common = {"batch_size": 6, "batch_concurrency": 1}
        if time_aggregation == "daily":
            kind_common = {"batch_size": 180, "batch_concurrency": 1}

        if ref["entity_type"] == "artifact":
            GeneratedModel.create(
                func=generated_entity,
                source=query._source.raw_sql,
                entrypoint_path=calling_file,
                config=config,
                name=f"metrics.{table_name}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "metrics_sample_date",
                    **kind_common,
                },
                dialect="clickhouse",
                columns=columns,
                grain=[
                    "metric",
                    "to_artifact_id",
                    "from_artifact_id",
                    "metrics_sample_date",
                ],
                cron=cron,
                start=start,
                additional_macros=additional_macros,
            )

        if ref["entity_type"] == "project":
            GeneratedModel.create(
                func=generated_entity,
                source=query._source.raw_sql,
                entrypoint_path=calling_file,
                config=config,
                name=f"metrics.{table_name}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "metrics_sample_date",
                    **kind_common,
                },
                dialect="clickhouse",
                columns=columns,
                grain=[
                    "metric",
                    "to_project_id",
                    "from_artifact_id",
                    "metrics_sample_date",
                ],
                cron=cron,
                start=start,
                additional_macros=additional_macros,
            )
        if ref["entity_type"] == "collection":
            GeneratedModel.create(
                func=generated_entity,
                source=query._source.raw_sql,
                entrypoint_path=calling_file,
                config=config,
                name=f"metrics.{table_name}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "metrics_sample_date",
                    **kind_common,
                },
                dialect="clickhouse",
                columns=columns,
                grain=[
                    "metric",
                    "to_collection_id",
                    "from_artifact_id",
                    "metrics_sample_date",
                ],
                cron=cron,
                start=start,
                additional_macros=additional_macros,
            )

    return all_tables


def timeseries_metrics(
    **raw_options: t.Unpack[TimeseriesMetricsOptions],
):
    calling_file = inspect.stack()[1].filename
    timeseries_sources = raw_options.get(
        "timeseries_sources", ["events_daily_to_artifact"]
    )
    assert timeseries_sources is not None

    metrics_queries = [
        MetricQuery.load(
            name=name,
            default_dialect=raw_options.get("default_dialect", "clickhouse"),
            source=query_def,
        )
        for name, query_def in raw_options["metric_queries"].items()
    ]

    # Build the dependency graph of all the metrics queries
    peer_table_map: t.Dict[str, str] = {}
    for query in metrics_queries:
        provided_refs = query.provided_dependency_refs
        for ref in provided_refs:
            peer_table_map[reference_to_str(ref)] = query.table_name(ref)

    all_tables: t.Dict[str, t.List[str]] = {
        "artifact": [],
        "project": [],
        "collection": [],
    }

    # Generate the models
    for query in metrics_queries:
        tables = generate_models_from_query(
            calling_file,
            query,
            default_dialect=raw_options.get("default_dialect", "clickhouse"),
            peer_table_map=peer_table_map,
            start=raw_options["start"],
            timeseries_sources=timeseries_sources,
        )
        for entity_type in all_tables.keys():
            all_tables[entity_type] = all_tables[entity_type] + tables[entity_type]

    # Join all of the models of the same entity type into the same view model
    for entity_type, tables in all_tables.items():
        GeneratedModel.create(
            func=join_all_of_entity_type,
            entrypoint_path=calling_file,
            config={
                "db": "metrics",
                "tables": tables,
                "columns": list(METRICS_COLUMNS_BY_ENTITY[entity_type].keys()),
            },
            name=f"metrics.timeseries_metrics_to_{entity_type}",
            kind="VIEW",
            dialect="clickhouse",
            start=raw_options["start"],
            columns=METRICS_COLUMNS_BY_ENTITY[entity_type],
        )


# def daily_timeseries_rolling_window_model(
#     **raw_options: t.Unpack[DailyTimeseriesRollingWindowOptions],
# ):
#     # We need to turn the options into something we can have easily pickled due
#     # to some sqlmesh execution environment management that I don't yet fully
#     # understand.
#     metric_queries = {
#         key: obj.to_input() for key, obj in raw_options["metric_queries"].items()
#     }
#     model_name = raw_options["model_name"]
#     trailing_days = raw_options["trailing_days"]

#     @model(
#         name=model_name,
#         is_sql=True,
#         kind={
#             "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
#             "time_column": "bucket_day",
#             "batch_size": 1,
#         },
#         dialect="clickhouse",
#         columns={
#             "bucket_day": exp.DataType.build("DATE", dialect="clickhouse"),
#             "event_source": exp.DataType.build("String", dialect="clickhouse"),
#             "to_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
#             "from_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
#             "metric": exp.DataType.build("String", dialect="clickhouse"),
#             "amount": exp.DataType.build("Float64", dialect="clickhouse"),
#         },
#         grain=["metric", "to_artifact_id", "from_artifact_id", "bucket_day"],
#         **(raw_options.get("model_options", {})),
#     )
#     def generated_model(evaluator: MacroEvaluator):
#         # Given a set of rolling metrics together. This will also ensure that
#         # all of the rolling windows are identical.

#         # Combine all of the queries
#         # together into a single query. Once all of the queries have been
#         # completed.
#         cte_suffix = uuid.uuid4().hex

#         subqueries: t.Dict[str, MetricQuery] = {}
#         for query_name, query_input in metric_queries.items():
#             query = MetricQueryDef.from_input(query_input)
#             subquery = subqueries[query_name] = MetricQuery.load(
#                 name=query_name, default_dialect="clickhouse", source=query
#             )

#         union_cte: t.Optional[exp.Query] = None

#         cte_column_select = [
#             "metrics_sample_date as bucket_day",
#             "to_artifact_id as to_artifact_id",
#             "from_artifact_id as from_artifact_id",
#             "event_source as event_source",
#             "metric as metric",
#             "CAST(amount AS Float64) as amount",
#         ]

#         top_level_select = exp.select(
#             "bucket_day",
#             "to_artifact_id",
#             "from_artifact_id",
#             "event_source",
#             "metric",
#             "amount",
#         ).from_(f"all_{cte_suffix}")

#         for name, subquery in subqueries.items():
#             # Validate the given dependencies
#             deps = subquery.peer_dependencies
#             for dep in deps:
#                 if dep not in subqueries:
#                     raise Exception(f"Missing dependency {dep} for metric query {name}")
#                 # Replace all the references to that table and replace it with a CTE reference
#                 replace_dep = replace_source_tables(
#                     sqlglot.to_table(f"peer.{dep}"),
#                     sqlglot.to_table(f"{dep}_{cte_suffix}"),
#                 )
#                 subquery.transform_expressions(replace_dep)

#             # Evaluate the expressions in the subquery
#             cte_name = f"{name}_{cte_suffix}"
#             evaluated = subquery.evaluate(
#                 evaluator, extra_vars=dict(trailing_days=trailing_days)
#             )
#             top_level_select = top_level_select.with_(cte_name, as_=evaluated)
#             unionable_select = sqlglot.select(*cte_column_select).from_(cte_name)
#             if not union_cte:
#                 union_cte = unionable_select
#             else:
#                 union_cte = union_cte.union(unionable_select, distinct=False)

#         if not union_cte:
#             raise Exception("no queries generated from the evaluated queries")
#         top_level_select = top_level_select.with_(f"all_{cte_suffix}", union_cte)
#         return top_level_select
#         return top_level_select
