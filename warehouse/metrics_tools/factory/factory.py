import contextlib
import inspect
import logging
import os
import textwrap
import typing as t
from dataclasses import dataclass, field
from datetime import datetime
from queue import PriorityQueue

import pandas as pd
import sqlglot as sql
from metrics_tools.compute.client import Client
from metrics_tools.compute.types import ExportType
from metrics_tools.definition import (
    MetricQuery,
    PeerMetricDependencyRef,
    TimeseriesMetricsOptions,
    reference_to_str,
)
from metrics_tools.joiner import JoinerTransform
from metrics_tools.macros import (
    metrics_end,
    metrics_entity_type_alias,
    metrics_entity_type_col,
    metrics_name,
    metrics_peer_ref,
    metrics_sample_date,
    metrics_start,
    relative_window_sample_date,
)
from metrics_tools.models import GeneratedModel, GeneratedPythonModel
from metrics_tools.runner import MetricsRunner
from metrics_tools.transformer import (
    IntermediateMacroEvaluatorTransform,
    SQLTransformer,
)
from metrics_tools.transformer.qualify import QualifyTransform
from metrics_tools.transformer.tables import ExecutionContextTableTransform
from metrics_tools.utils import env
from metrics_tools.utils.logging import add_metrics_tools_to_sqlmesh_logging
from metrics_tools.utils.tables import create_dependent_tables_map
from sqlglot import exp
from sqlmesh import ExecutionContext
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.macros import MacroEvaluator
from sqlmesh.core.model import ModelKindName

logger = logging.getLogger(__name__)

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../metrics_mesh/oso_metrics"))

TIME_AGGREGATION_TO_CRON = {
    "daily": "@daily",
    "monthly": "@monthly",
    "weekly": "@weekly",
}
METRICS_COLUMNS_BY_ENTITY: t.Dict[str, t.Dict[str, exp.DataType]] = {
    "artifact": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="duckdb"),
        "event_source": exp.DataType.build("STRING", dialect="duckdb"),
        "to_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "from_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "metric": exp.DataType.build("STRING", dialect="duckdb"),
        "amount": exp.DataType.build("DOUBLE", dialect="duckdb"),
    },
    "project": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="duckdb"),
        "event_source": exp.DataType.build("STRING", dialect="duckdb"),
        "to_project_id": exp.DataType.build("STRING", dialect="duckdb"),
        "from_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "metric": exp.DataType.build("STRING", dialect="duckdb"),
        "amount": exp.DataType.build("DOUBLE", dialect="duckdb"),
    },
    "collection": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="duckdb"),
        "event_source": exp.DataType.build("STRING", dialect="duckdb"),
        "to_collection_id": exp.DataType.build("STRING", dialect="duckdb"),
        "from_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "metric": exp.DataType.build("STRING", dialect="duckdb"),
        "amount": exp.DataType.build("DOUBLE", dialect="duckdb"),
    },
}


@contextlib.contextmanager
def metric_ref_evaluator_context(
    evaluator: MacroEvaluator,
    ref: PeerMetricDependencyRef,
    extra_vars: t.Optional[t.Dict[str, t.Any]] = None,
):
    before = evaluator.locals.copy()
    evaluator.locals.update(extra_vars or {})
    evaluator.locals.update(
        {
            "rolling_window": ref.get("window"),
            "rolling_unit": ref.get("unit"),
            "time_aggregation": ref.get("time_aggregation"),
            "entity_type": ref.get("entity_type"),
        }
    )
    try:
        yield
    finally:
        evaluator.locals = before


class MetricQueryConfig(t.TypedDict):
    table_name: str
    ref: PeerMetricDependencyRef
    rendered_query: exp.Expression
    vars: t.Dict[str, t.Any]
    query: MetricQuery


class MetricsCycle(Exception):
    pass


class TimeseriesMetrics:
    @classmethod
    def from_raw_options(cls, **raw_options: t.Unpack[TimeseriesMetricsOptions]):
        timeseries_sources = raw_options.get(
            "timeseries_sources", ["events_daily_to_artifact"]
        )
        assert timeseries_sources is not None
        queries_dir = raw_options.get("queries_dir", QUERIES_DIR)
        assert queries_dir is not None

        enabled_queries = filter(
            lambda item: item[1].enabled, raw_options["metric_queries"].items()
        )

        metrics_queries = [
            MetricQuery.load(
                name=name,
                default_dialect=raw_options.get("default_dialect", "duckdb"),
                source=query_def,
                queries_dir=queries_dir,
            )
            for name, query_def in enabled_queries
        ]

        # Build the dependency graph of all the metrics queries
        peer_table_map: t.Dict[str, str] = {}
        for query in metrics_queries:
            provided_refs = query.provided_dependency_refs
            for ref in provided_refs:
                peer_table_map[reference_to_str(ref)] = query.table_name(ref)

        return cls(timeseries_sources, metrics_queries, peer_table_map, raw_options)

    def __init__(
        self,
        timeseries_sources: t.List[str],
        metrics_queries: t.List[MetricQuery],
        peer_table_map: t.Dict[str, str],
        raw_options: TimeseriesMetricsOptions,
    ):
        marts_tables: t.Dict[str, t.List[str]] = {
            "artifact": [],
            "project": [],
            "collection": [],
        }
        self._timeseries_sources = timeseries_sources
        self._metrics_queries = metrics_queries
        self._peer_table_map = peer_table_map
        self._marts_tables = marts_tables
        self._raw_options = raw_options
        self._rendered = False
        self._rendered_queries: t.Dict[str, MetricQueryConfig] = {}

    @property
    def catalog(self):
        """The catalog (sometimes db name) to use for rendered queries"""
        return self._raw_options["catalog"]

    def generate_queries(self):
        if self._rendered:
            return self._rendered_queries

        queries: t.Dict[str, MetricQueryConfig] = {}
        for query in self._metrics_queries:
            queries.update(
                self._generate_metrics_queries(query, self._peer_table_map, "metrics")
            )
        self._rendered_queries = queries
        self._rendered = True
        return queries

    def _generate_metrics_queries(
        self,
        query: MetricQuery,
        peer_table_map: t.Dict[str, str],
        db_name: str,
    ):
        """Given a MetricQuery, generate all of the queries for it's given dimensions"""
        # Turn the source into a dict so it can be used in the sqlmesh context
        refs = query.provided_dependency_refs

        marts_tables = self._marts_tables

        queries: t.Dict[str, MetricQueryConfig] = {}
        for ref in refs:
            table_name = query.table_name(ref)

            if not query.is_intermediate:
                marts_tables[ref["entity_type"]].append(table_name)

            additional_macros = [
                metrics_peer_ref,
                metrics_entity_type_col,
                metrics_entity_type_alias,
                relative_window_sample_date,
                (metrics_name, ["metric_name"]),
            ]

            evaluator_variables: t.Dict[str, t.Any] = {
                "generated_metric_name": ref["name"],
                "entity_type": ref["entity_type"],
                "time_aggregation": ref.get("time_aggregation", None),
                "rolling_window": ref.get("window", None),
                "rolling_unit": ref.get("unit", None),
                "$$peer_table_map": peer_table_map,
                "$$peer_db": db_name,
            }
            evaluator_variables.update(query.vars)

            transformer = SQLTransformer(
                disable_qualify=True,
                transforms=[
                    IntermediateMacroEvaluatorTransform(
                        additional_macros,
                        variables=evaluator_variables,
                    ),
                    QualifyTransform(
                        validate_qualify_columns=False, allow_partial_qualification=True
                    ),
                    JoinerTransform(
                        ref["entity_type"],
                        self._timeseries_sources,
                    ),
                    QualifyTransform(),
                ],
            )

            rendered_query = transformer.transform([query.query_expression])

            assert rendered_query is not None
            assert len(rendered_query) == 1
            queries[table_name] = MetricQueryConfig(
                table_name=table_name,
                ref=ref,
                rendered_query=rendered_query[0],
                vars=query._source.vars or {},
                query=query,
            )
        return queries

    def generate_ordered_queries(self):
        """Perform a topological sort on all the queries within metrics"""

        @dataclass(order=True)
        class MetricQueryConfigQueueItem:
            depth: int
            config: MetricQueryConfig = field(compare=False)

        # hack for now. We actually need to resolve the queries to do proper
        # ordering but this is mostly for testing.
        sources = self._timeseries_sources
        queries = self.generate_queries()

        queue = PriorityQueue()

        visited: t.Dict[str, int] = {}
        cycle_lock: t.Dict[str, bool] = {}
        dependencies: t.Dict[str, t.Set[str]] = {}

        def queue_query(name: str):
            if name in cycle_lock:
                raise MetricsCycle("Invalid metrics. Cycle detected")

            if name in visited:
                return visited[name]
            cycle_lock[name] = True

            query_config = queries[name]
            rendered_query = query_config["rendered_query"]
            depth = 0
            tables = rendered_query.find_all(exp.Table)
            parents = set()
            for table in tables:
                db_name = table.db
                if isinstance(table.db, exp.Identifier):
                    db_name = table.db.this
                table_name = table.this.this

                if db_name != "metrics":
                    continue

                parents.add(table_name)
                if table_name in sources:
                    logger.debug(f"skipping known time series source {table_name}")
                    continue

                if queries.get(table_name) is None:
                    logger.debug(
                        f"skipping table {name}. probably an external table to metrics"
                    )
                    continue

                try:
                    parent_depth = queue_query(table_name)
                except MetricsCycle:
                    parent_query = queries[table_name]["rendered_query"]
                    raise MetricsCycle(
                        textwrap.dedent(
                            f"""Cycle from {name} to {table_name}: 
                         ---
                        {name}:
                        {rendered_query.sql(dialect="duckdb", pretty=True)}
                        ----
                        parent:
                        {parent_query.sql(dialect="duckdb", pretty=True)}
                        """
                        )
                    )
                if parent_depth + 1 > depth:
                    depth = parent_depth + 1
            queue.put(MetricQueryConfigQueueItem(depth, query_config))
            visited[name] = depth
            dependencies[name] = parents
            del cycle_lock[name]
            return depth

        for name in queries.keys():
            if visited.get(name) is None:
                queue_query(name)

        while not queue.empty():
            item = t.cast(MetricQueryConfigQueueItem, queue.get())
            depth = item.depth
            query_config = item.config
            yield (depth, query_config, dependencies[query_config["table_name"]])

    def generate_models(self, calling_file: str):
        """Generates sqlmesh models for all the configured metrics definitions"""
        # Generate the models

        for _, query_config, dependencies in self.generate_ordered_queries():
            self.generate_model_for_rendered_query(
                calling_file, query_config, dependencies
            )

        # Join all of the models of the same entity type into the same view model
        for entity_type, tables in self._marts_tables.items():
            GeneratedModel.create(
                func=join_all_of_entity_type,
                entrypoint_path=calling_file,
                config={
                    "db": self.catalog,
                    "tables": tables,
                    "columns": list(METRICS_COLUMNS_BY_ENTITY[entity_type].keys()),
                },
                name=f"metrics.timeseries_metrics_to_{entity_type}",
                kind="VIEW",
                dialect="clickhouse",
                start=self._raw_options["start"],
                columns={
                    k: METRICS_COLUMNS_BY_ENTITY[entity_type][k]
                    for k in filter(
                        lambda col: col not in ["event_source"],
                        METRICS_COLUMNS_BY_ENTITY[entity_type].keys(),
                    )
                },
                enabled=self._raw_options.get("enabled", True),
            )
        logger.info("model generation complete")

    def generate_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        query = query_config["query"]
        match query.metric_type:
            case "rolling":
                self.generate_rolling_python_model_for_rendered_query(
                    calling_file, query_config, dependencies
                )
            case "time_aggregation":
                self.generate_time_aggregation_model_for_rendered_query(
                    calling_file, query_config, dependencies
                )

    def generate_rolling_python_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        depends_on = set()
        for dep in dependencies:
            depends_on.add(f"{self.catalog}.{dep}")

        ref = query_config["ref"]
        query = query_config["query"]

        columns = METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]

        kind_common = {"batch_concurrency": 1}
        partitioned_by = ("day(metrics_sample_date)",)
        window = ref.get("window")
        assert window is not None
        assert query._source.rolling
        cron = query._source.rolling["cron"]

        grain = [
            "metric",
            f"to_{ref['entity_type']}_id",
            "event_source",
            "from_artifact_id",
            "metrics_sample_date",
        ]

        return GeneratedPythonModel.create(
            name=f"{self.catalog}.{query_config['table_name']}",
            func=generated_rolling_query_proxy,
            entrypoint_path=calling_file,
            additional_macros=self.generated_model_additional_macros,
            variables=self.serializable_config(query_config),
            depends_on=depends_on,
            columns=columns,
            kind={
                "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                "time_column": "metrics_sample_date",
                **kind_common,
            },
            partitioned_by=partitioned_by,
            cron=cron,
            start=self._raw_options["start"],
            grain=grain,
            imports={"pd": pd, "generated_rolling_query": generated_rolling_query},
            enabled=self._raw_options.get("enabled", True),
        )

    def generate_time_aggregation_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        """Generate model for time aggregation models"""
        # Use a simple python sql model to generate the time_aggregation model
        config = self.serializable_config(query_config)

        ref = query_config["ref"]

        columns = METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]

        time_aggregation = ref.get("time_aggregation")
        assert time_aggregation is not None

        kind_common = {"batch_concurrency": 1}
        kind_options = {"lookback": 7, **kind_common}
        partitioned_by = ("day(metrics_sample_date)",)

        if time_aggregation == "weekly":
            kind_options = {"lookback": 7, **kind_common}
        if time_aggregation == "monthly":
            kind_options = {"lookback": 1, **kind_common}
            partitioned_by = ("month(metrics_sample_date)",)

        grain = [
            "metric",
            f"to_{ref['entity_type']}_id",
            "from_artifact_id",
            "event_source",
            "metrics_sample_date",
        ]
        cron = TIME_AGGREGATION_TO_CRON[time_aggregation]

        GeneratedModel.create(
            func=generated_query,
            entrypoint_path=calling_file,
            config=config,
            name=f"{self.catalog}.{query_config['table_name']}",
            kind={
                "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                "time_column": "metrics_sample_date",
                **kind_options,
            },
            dialect="clickhouse",
            columns=columns,
            grain=grain,
            cron=cron,
            start=self._raw_options["start"],
            additional_macros=self.generated_model_additional_macros,
            partitioned_by=partitioned_by,
            enabled=self._raw_options.get("enabled", True),
        )

    def serializable_config(self, query_config: MetricQueryConfig):
        # Use a simple python sql model to generate the time_aggregation model
        config: t.Dict[str, t.Any] = t.cast(dict, query_config.copy())

        # MetricQuery can't be serialized. Remove it. It's not needed
        del config["query"]
        # Apparently expressions also cannot be serialized.
        del config["rendered_query"]
        config["rendered_query_str"] = query_config["rendered_query"].sql(
            dialect="duckdb"
        )
        return config

    @property
    def generated_model_additional_macros(
        self,
    ) -> t.List[t.Callable | t.Tuple[t.Callable, t.List[str]]]:
        return [metrics_end, metrics_start, metrics_sample_date]


# Specifically for testing. This is used if the
# `metrics_tools.utils.testing.ENABLE_TIMESERIES_DEBUG` variable is true. This
# is for loading all of the timeseries metrics from inside the metrics_mesh
# project and inspecting the actually rendered queries for testing purposes.
# It's a bit of a hack but it will work for the current purposes.
GLOBAL_TIMESERIES_METRICS: t.Dict[str, TimeseriesMetrics] = {}


def timeseries_metrics(
    **raw_options: t.Unpack[TimeseriesMetricsOptions],
):
    from metrics_tools.utils.testing import ENABLE_TIMESERIES_DEBUG

    add_metrics_tools_to_sqlmesh_logging()
    logger.info("loading timeseries metrics")
    frame_info = inspect.stack()[1]
    calling_file = frame_info.filename
    timeseries_metrics = TimeseriesMetrics.from_raw_options(**raw_options)

    if ENABLE_TIMESERIES_DEBUG:
        GLOBAL_TIMESERIES_METRICS[calling_file] = timeseries_metrics

    return timeseries_metrics.generate_models(calling_file)


def join_all_of_entity_type(
    evaluator: MacroEvaluator, *, db: str, tables: t.List[str], columns: t.List[str]
):
    # A bit of a hack but we know we have a "metric" column. We want to
    # transform this metric id to also include the event_source as a prefix to
    # that metric id in the joined table
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


def generated_query(
    evaluator: MacroEvaluator,
    *,
    rendered_query_str: str,
    ref: PeerMetricDependencyRef,
    table_name: str,
    vars: t.Dict[str, t.Any],
):
    """Simple generated query executor for metrics queries"""

    with metric_ref_evaluator_context(evaluator, ref, vars):
        result = evaluator.transform(parse_one(rendered_query_str))
    return result


def generated_rolling_query(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    ref: PeerMetricDependencyRef,
    vars: t.Dict[str, t.Any],
    rendered_query_str: str,
    table_name: str,
    sqlmesh_vars: t.Dict[str, t.Any],
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
    locals = vars.copy()
    locals.update(sqlmesh_vars)

    mcs_enabled = env.ensure_bool("SQLMESH_MCS_ENABLED", False)
    if not mcs_enabled:
        runner = MetricsRunner.from_sqlmesh_context(context, query, ref, locals)
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
            logger.debug(f"table={table_name} yielding rows {count}")
            yield df
        logger.debug(f"table={table_name} yielded rows{total}")
    else:
        logger.info("metrics calculation service enabled")

        mcs_url = env.required_str("SQLMESH_MCS_URL")
        mcs_client = Client(url=mcs_url)

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
            batch_size=1,
            columns=columns,
            ref=ref,
            locals=sqlmesh_vars,
            dependent_tables_map=create_dependent_tables_map(
                context, rendered_query_str
            ),
        )

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


def generated_rolling_query_proxy(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    ref: PeerMetricDependencyRef,
    vars: t.Dict[str, t.Any],
    rendered_query_str: str,
    table_name: str,
    sqlmesh_vars: t.Dict[str, t.Any],
    **kwargs,
) -> t.Iterator[pd.DataFrame | exp.Expression]:
    """This acts as the proxy to the actual function that we'd call for
    the metrics model."""

    yield from generated_rolling_query(
        context,
        start,
        end,
        execution_time,
        ref,
        vars,
        rendered_query_str,
        table_name,
        sqlmesh_vars,
        context.gateway,
        # Change the following variable to force reevaluation. Hack for now.
        "version=v5",
    )
