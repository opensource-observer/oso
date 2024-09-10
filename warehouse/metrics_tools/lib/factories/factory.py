import typing as t
import os
import inspect

from sqlglot import exp
from sqlmesh.core.model import ModelKindName
from metrics_tools.lib.factories.definition import (
    MetricQuery,
    TimeseriesMetricsOptions,
    reference_to_str,
    GeneratedArtifactConfig,
)
from metrics_tools.models import GeneratedModel

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../oso_metrics"))

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]


ROLLUP_TO_CRON = {"daily": "@daily", "monthly": "@monthly", "weekly": "@weekly"}


def generate_models_from_query(
    calling_file: str,
    query: MetricQuery,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
):
    # Turn the source into a dict so it can be used in the sqlmesh context
    query_def_as_input = query._source.to_input()
    query_reference_name = query.reference_name
    refs = query.provided_dependency_refs
    for ref in refs:
        cron = "@daily"
        rollup = ref.get("rollup")
        window = ref.get("window")
        if rollup:
            cron = ROLLUP_TO_CRON[rollup]
        else:
            if not window:
                raise Exception("window or rollup must be set")
            assert query._source.rolling
            cron = query._source.rolling["cron"]

        config = GeneratedArtifactConfig(
            query_reference_name=query_reference_name,
            query_def_as_input=query_def_as_input,
            default_dialect=default_dialect,
            peer_table_map=peer_table_map,
            ref=ref,
        )
        if ref["entity_type"] == "artifact":
            GeneratedModel.create(
                func_name="generated_entity",
                import_module="metrics_tools.lib.factories.definition",
                entrypoint_path=calling_file,
                config=config,
                name=f"metrics.{query.table_name(ref)}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "bucket_day",
                    "batch_size": 1,
                },
                dialect="clickhouse",
                columns={
                    "bucket_day": exp.DataType.build("DATE", dialect="clickhouse"),
                    "event_source": exp.DataType.build("String", dialect="clickhouse"),
                    "to_artifact_id": exp.DataType.build(
                        "String", dialect="clickhouse"
                    ),
                    "from_artifact_id": exp.DataType.build(
                        "String", dialect="clickhouse"
                    ),
                    "metric": exp.DataType.build("String", dialect="clickhouse"),
                    "amount": exp.DataType.build("Float64", dialect="clickhouse"),
                },
                grain=["metric", "to_artifact_id", "from_artifact_id", "bucket_day"],
                cron=cron,
            )

        if ref["entity_type"] == "project":
            GeneratedModel.create(
                func_name="generated_entity",
                import_module="metrics_tools.lib.factories.definition",
                entrypoint_path=calling_file,
                config=config,
                name=f"metrics.{query.table_name(ref)}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "bucket_day",
                    "batch_size": 1,
                },
                dialect="clickhouse",
                columns={
                    "bucket_day": exp.DataType.build("DATE", dialect="clickhouse"),
                    "event_source": exp.DataType.build("String", dialect="clickhouse"),
                    "to_project_id": exp.DataType.build("String", dialect="clickhouse"),
                    "from_artifact_id": exp.DataType.build(
                        "String", dialect="clickhouse"
                    ),
                    "metric": exp.DataType.build("String", dialect="clickhouse"),
                    "amount": exp.DataType.build("Float64", dialect="clickhouse"),
                },
                grain=["metric", "to_project_id", "from_artifact_id", "bucket_day"],
                cron=cron,
            )
        if ref["entity_type"] == "collection":
            GeneratedModel.create(
                func_name="generated_entity",
                import_module="metrics_tools.lib.factories.definition",
                entrypoint_path=calling_file,
                config=config,
                name=f"metrics.{query.table_name(ref)}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "bucket_day",
                    "batch_size": 1,
                },
                dialect="clickhouse",
                columns={
                    "bucket_day": exp.DataType.build("DATE", dialect="clickhouse"),
                    "event_source": exp.DataType.build("String", dialect="clickhouse"),
                    "to_collection_id": exp.DataType.build(
                        "String", dialect="clickhouse"
                    ),
                    "from_artifact_id": exp.DataType.build(
                        "String", dialect="clickhouse"
                    ),
                    "metric": exp.DataType.build("String", dialect="clickhouse"),
                    "amount": exp.DataType.build("Float64", dialect="clickhouse"),
                },
                grain=["metric", "to_collection_id", "from_artifact_id", "bucket_day"],
                cron=cron,
            )


def timeseries_metrics(
    **raw_options: t.Unpack[TimeseriesMetricsOptions],
):
    calling_file = inspect.stack()[1].filename

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

    # Generate the models
    for query in metrics_queries:
        generate_models_from_query(
            calling_file,
            query,
            default_dialect=raw_options.get("default_dialect", "clickhouse"),
            peer_table_map=peer_table_map,
        )

    # Join all of the models of the same entity type into the same


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
#             "metrics_bucket_date as bucket_day",
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
