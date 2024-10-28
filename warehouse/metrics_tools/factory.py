import inspect
import typing as t

from metrics_tools.joiner import JoinerTransform
from metrics_tools.transformer.base import SQLTransformer
from metrics_tools.transformer.intermediate import IntermediateMacroEvaluatorTransform
from sqlmesh.core.macros import MacroEvaluator
from sqlmesh.utils.date import TimeLike
from sqlmesh.core.model import ModelKindName
from sqlglot import exp

from .definition import MetricQuery, TimeseriesMetricsOptions, reference_to_str
from .models import GeneratedModel

from .lib.factories.macros import (
    metrics_entity_type_col,
    metrics_name,
    relative_window_sample_date,
    metrics_entity_type_alias,
)

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


def generate_metrics_queries(
    query: MetricQuery,
    peer_table_map: t.Dict[str, str],
    db_name: str,
):
    # Turn the source into a dict so it can be used in the sqlmesh context
    refs = query.provided_dependency_refs

    all_tables: t.Dict[str, t.List[str]] = {
        "artifact": [],
        "project": [],
        "collection": [],
    }

    queries: t.Dict[str, exp.Expression] = {}
    for ref in refs:
        table_name = query.table_name(ref)

        all_tables[ref["entity_type"]].append(table_name)

        additional_macros = [
            metrics_entity_type_col,
            metrics_entity_type_alias,
            relative_window_sample_date,
            (metrics_name, ["metric_name"]),
        ]

        transformer = SQLTransformer(
            transforms=[
                JoinerTransform(
                    ref["entity_type"],
                ),
                IntermediateMacroEvaluatorTransform(
                    additional_macros,
                    variables={
                        "generated_metric_name": ref["name"],
                        "entity_type": ref["entity_type"],
                        "time_aggregation": ref.get("time_aggregation", None),
                        "rolling_window": ref.get("window", None),
                        "rolling_unit": ref.get("unit", None),
                        "$$peer_table_map": peer_table_map,
                        "$$peer_db": db_name,
                    },
                ),
            ]
        )

        rendered_query = transformer.transform([query.query_expression])
        print("-----------------")
        print(rendered_query)
        print("-----------------")

        assert rendered_query is not None
        assert len(rendered_query) == 1
        queries[table_name] = rendered_query[0]
    return queries


def generate_metric_models(
    calling_file: str,
    query: MetricQuery,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
    start: TimeLike,
    timeseries_sources: t.List[str],
):
    # Turn the source into a dict so it can be used in the sqlmesh context
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

        table_name = query.table_name(ref)
        all_tables[ref["entity_type"]].append(table_name)
        columns = METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]
        additional_macros = [
            metrics_entity_type_col,
            metrics_entity_type_alias,
            relative_window_sample_date,
            (metrics_name, ["metric_name"]),
        ]

        kind_common = {"batch_size": 1}
        partitioned_by = ("day(metrics_sample_date)",)

        # Due to how the schedulers work for sqlmesh we actually can't batch if
        # we're using a weekly cron for a time aggregation. In order to have
        # this work we just adjust the start/end time for the
        # metrics_start/metrics_end and also give a large enough batch time to
        # fit a few weeks. This ensures there's on missing data
        if time_aggregation == "weekly":
            kind_common = {"batch_size": 182, "lookback": 7}
        if time_aggregation == "monthly":
            kind_common = {"batch_size": 6}
            partitioned_by = ("month(metrics_sample_date)",)
        if time_aggregation == "daily":
            kind_common = {"batch_size": 180}

        print("ADDITIONAL MACROS")
        print(additional_macros)

        transformer = SQLTransformer(
            transforms=[
                IntermediateMacroEvaluatorTransform(
                    additional_macros,
                    variables={
                        "entity_type": ref["entity_type"],
                        "time_aggregation": ref.get("time_aggregation", None),
                        "rolling_window": ref.get("window", None),
                        "rolling_unit": ref.get("unit", None),
                    },
                ),
                JoinerTransform(
                    ref["entity_type"],
                ),
                IntermediateMacroEvaluatorTransform(
                    additional_macros,
                    variables={
                        "entity_type": ref["entity_type"],
                        "time_aggregation": ref.get("time_aggregation", None),
                        "rolling_window": ref.get("window", None),
                        "rolling_unit": ref.get("unit", None),
                    },
                ),
            ]
        )

        rendered_query = transformer.transform([query.query_expression])
        print(rendered_query)

        if ref["entity_type"] == "artifact":
            GeneratedModel.create(
                func=generated_query,
                source=query._source.raw_sql,
                entrypoint_path=calling_file,
                config={},
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
                partitioned_by=partitioned_by,
            )

        if ref["entity_type"] == "project":
            GeneratedModel.create(
                func=generated_query,
                source=query._source.raw_sql,
                entrypoint_path=calling_file,
                config={},
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
                partitioned_by=partitioned_by,
            )
        if ref["entity_type"] == "collection":
            GeneratedModel.create(
                func=generated_query,
                source=query._source.raw_sql,
                entrypoint_path=calling_file,
                config={},
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
                partitioned_by=partitioned_by,
            )

    return all_tables


def generated_query(evaluator: MacroEvaluator, query: exp.Expression):
    return query


class TimeseriesMetrics:
    @classmethod
    def from_raw_options(cls, **raw_options: t.Unpack[TimeseriesMetricsOptions]):
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
        return cls(
            timeseries_sources, metrics_queries, peer_table_map, all_tables, raw_options
        )

    def __init__(
        self,
        timeseries_sources: t.List[str],
        metrics_queries: t.List[MetricQuery],
        peer_table_map: t.Dict[str, str],
        all_tables: t.Dict[str, t.List[str]],
        raw_options: TimeseriesMetricsOptions,
    ):
        self._timeseries_sources = timeseries_sources
        self._metrics_queries = metrics_queries
        self._peer_table_map = peer_table_map
        self._all_tables = all_tables
        self._raw_options = raw_options

    def generate_models(self, calling_file: str):
        # Generate the models
        for query in self._metrics_queries:
            tables = generate_metric_models(
                calling_file,
                query,
                default_dialect=self._raw_options.get("default_dialect", "clickhouse"),
                peer_table_map=self._peer_table_map,
                start=self._raw_options["start"],
                timeseries_sources=self._timeseries_sources,
            )
            if not query.is_intermediate:
                for entity_type in self._all_tables.keys():
                    self._all_tables[entity_type] = (
                        self._all_tables[entity_type] + tables[entity_type]
                    )

        # # Join all of the models of the same entity type into the same view model
        # for entity_type, tables in self._all_tables.items():
        #     GeneratedModel.create(
        #         func=join_all_of_entity_type,
        #         entrypoint_path=calling_file,
        #         config={
        #             "db": "metrics",
        #             "tables": tables,
        #             "columns": list(METRICS_COLUMNS_BY_ENTITY[entity_type].keys()),
        #         },
        #         name=f"metrics.timeseries_metrics_to_{entity_type}",
        #         kind="VIEW",
        #         dialect="clickhouse",
        #         start=self._raw_options["start"],
        #         columns={
        #             k: METRICS_COLUMNS_BY_ENTITY[entity_type][k]
        #             for k in filter(
        #                 lambda col: col not in ["event_source"],
        #                 METRICS_COLUMNS_BY_ENTITY[entity_type].keys(),
        #             )
        #         },
        #     )

    def generate_queries(self):
        queries: t.Dict[str, exp.Expression] = {}
        for query in self._metrics_queries:
            queries.update(
                generate_metrics_queries(query, self._peer_table_map, "metrics")
            )
        return queries


def timeseries_metrics(
    **raw_options: t.Unpack[TimeseriesMetricsOptions],
):
    calling_file = inspect.stack()[1].filename
    timeseries_metrics = TimeseriesMetrics.from_raw_options(**raw_options)
    return timeseries_metrics.generate_models(calling_file)
