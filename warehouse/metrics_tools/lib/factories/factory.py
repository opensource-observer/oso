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

        # Clean up the peer_table_map (this is a hack to prevent unnecessary
        # runs when the metrics factory is updated)
        query_dependencies = query.dependencies(ref, peer_table_map)
        # So much of this needs to be refactored but for now this is to ensure
        # that in some way that the dict doesn't randomly "change". I don't
        # think this will be consistent between python machines but let's see
        # for now.
        reduced_peer_table_tuples = [(k, peer_table_map[k]) for k in query_dependencies]
        reduced_peer_table_tuples.sort()

        config = GeneratedArtifactConfig(
            query_reference_name=query_reference_name,
            query_def_as_input=query_def_as_input,
            default_dialect=default_dialect,
            peer_table_tuples=reduced_peer_table_tuples,
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
                partitioned_by=partitioned_by,
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
                partitioned_by=partitioned_by,
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
                partitioned_by=partitioned_by,
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
        if not query.is_intermediate:
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
            columns={
                k: METRICS_COLUMNS_BY_ENTITY[entity_type][k]
                for k in filter(
                    lambda col: col not in ["event_source"],
                    METRICS_COLUMNS_BY_ENTITY[entity_type].keys(),
                )
            },
        )
