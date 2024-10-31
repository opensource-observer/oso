import contextlib
from datetime import datetime
import inspect
import logging
import os
from queue import PriorityQueue
import typing as t
import textwrap
import pandas as pd
from dataclasses import dataclass, field

from sqlmesh import ExecutionContext
from sqlmesh.core.macros import MacroEvaluator
from sqlmesh.core.model import ModelKindName
import sqlglot as sql
from sqlglot import exp

from metrics_tools.joiner import JoinerTransform
from metrics_tools.transformer import (
    SQLTransformer,
    IntermediateMacroEvaluatorTransform,
)
from metrics_tools.transformer.qualify import QualifyTransform
from metrics_tools.definition import (
    MetricQuery,
    PeerMetricDependencyRef,
    TimeseriesMetricsOptions,
    reference_to_str,
)
from metrics_tools.models import (
    GeneratedModel,
    GeneratedPythonModel,
)
from metrics_tools.factory.macros import (
    metrics_end,
    metrics_entity_type_col,
    metrics_name,
    metrics_sample_date,
    metrics_start,
    relative_window_sample_date,
    metrics_entity_type_alias,
    metrics_peer_ref,
)

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
                default_dialect=raw_options.get("default_dialect", "clickhouse"),
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
                    QualifyTransform(),
                    JoinerTransform(
                        ref["entity_type"],
                    ),
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

                if table_name in sources:
                    continue
                parents.add(table_name)

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
            )
        print("model generation complete")

    def generate_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        query = query_config["query"]
        match query.metric_type:
            case "rolling":
                if query.use_python_model:
                    self.generate_rolling_python_model_for_rendered_query(
                        calling_file, query_config, dependencies
                    )
                else:
                    self.generate_rolling_model_for_rendered_query(
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

        kind_common = {"batch_size": 1}
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
            func=generated_rolling_query,
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
        )

    def generate_rolling_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        config = self.serializable_config(query_config)

        ref = query_config["ref"]
        query = query_config["query"]

        columns = METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]

        kind_common = {"batch_size": 1}
        partitioned_by = ("day(metrics_sample_date)",)
        window = ref.get("window")
        assert window is not None
        assert query._source.rolling
        cron = query._source.rolling["cron"]

        grain = [
            "metric",
            f"to_{ref['entity_type']}_id",
            "from_artifact_id",
            "event_source",
            "metrics_sample_date",
        ]

        GeneratedModel.create(
            func=generated_query,
            entrypoint_path=calling_file,
            config=config,
            name=f"{self.catalog}.{query_config['table_name']}",
            kind={
                "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                "time_column": "metrics_sample_date",
                **kind_common,
            },
            dialect="clickhouse",
            columns=columns,
            grain=grain,
            cron=cron,
            start=self._raw_options["start"],
            additional_macros=self.generated_model_additional_macros,
            partitioned_by=partitioned_by,
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

        kind_options = {"batch_size": 180, "lookback": 7}
        partitioned_by = ("day(metrics_sample_date)",)

        if time_aggregation == "weekly":
            kind_options = {"batch_size": 182, "lookback": 7}
        if time_aggregation == "monthly":
            kind_options = {"batch_size": 6, "lookback": 1}
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
        print(f"config={config}")
        return config

    @property
    def generated_model_additional_macros(
        self,
    ) -> t.List[t.Callable | t.Tuple[t.Callable, t.List[str]]]:
        return [metrics_end, metrics_start, metrics_sample_date]


def timeseries_metrics(
    **raw_options: t.Unpack[TimeseriesMetricsOptions],
):
    calling_file = inspect.stack()[1].filename
    timeseries_metrics = TimeseriesMetrics.from_raw_options(**raw_options)
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
    from sqlmesh.core.dialect import parse_one

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
    **kwargs,
) -> pd.DataFrame:
    print(f"printing start={start}")

    data = {
        "metrics_sample_date": [end],
        "metric": ["metric"],
        "event_source": ["TEST"],
        f"to_{ref['entity_type']}_id": ["artifact_1"],
        "from_artifact_id": ["artifact_2"],
        "amount": [1.0],
    }
    return pd.DataFrame(data)
