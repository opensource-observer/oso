import functools
import inspect
import logging
import os
import textwrap
import typing as t
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from queue import PriorityQueue

from metrics_tools.definition import (
    MetricMetadata,
    MetricQuery,
    PeerMetricDependencyRef,
    TimeseriesMetricsOptions,
    reference_to_str,
)
from metrics_tools.factory import constants
from metrics_tools.joiner import JoinerTransform
from metrics_tools.macros import (
    metrics_end,
    metrics_entity_type_alias,
    metrics_entity_type_col,
    metrics_entity_type_table,
    metrics_name,
    metrics_peer_ref,
    metrics_sample_date,
    metrics_sample_interval_length,
    metrics_start,
    relative_window_sample_date,
)
from metrics_tools.models.tools import MacroOverridingModel
from metrics_tools.transformer import (
    IntermediateMacroEvaluatorTransform,
    SQLTransformer,
)
from metrics_tools.transformer.qualify import QualifyTransform
from metrics_tools.utils.logging import add_metrics_tools_to_sqlmesh_logging
from sqlglot import exp
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.macros import MacroEvaluator
from sqlmesh.core.model import ModelKindName

logger = logging.getLogger(__name__)

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../oso_sqlmesh/oso_metrics"))


class MetricQueryConfig(t.TypedDict):
    table_name: str
    ref: PeerMetricDependencyRef
    rendered_query: exp.Expression
    vars: t.Dict[str, t.Any]
    query: MetricQuery
    metadata: t.Optional[MetricMetadata]
    incremental: bool
    additional_tags: t.List[str]


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
        timeseries_mart_tables: t.Dict[str, t.List[str]] = {
            "artifact": [],
            "project": [],
            "collection": [],
        }
        key_metrics_mart_tables: t.Dict[str, t.List[str]] = {
            "artifact": [],
            "project": [],
            "collection": [],
        }
        self._timeseries_sources = timeseries_sources
        self._metrics_queries = metrics_queries
        self._peer_table_map = peer_table_map
        self._timeseries_marts_tables = timeseries_mart_tables
        self._key_metrics_marts_tables = key_metrics_mart_tables
        self._raw_options = raw_options
        self._rendered = False
        self._rendered_queries: t.Dict[str, MetricQueryConfig] = {}

    @property
    def schema(self):
        """The schema (sometimes db name) to use for rendered queries"""
        return self._raw_options["schema"]

    def generate_queries(self):
        if self._rendered:
            return self._rendered_queries

        queries: t.Dict[str, MetricQueryConfig] = {}
        for query in self._metrics_queries:
            queries.update(
                self._generate_metrics_queries(query, self._peer_table_map, self.schema)
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

        timeseries_mart_tables = self._timeseries_marts_tables
        key_metrics_mart_tables = self._key_metrics_marts_tables

        queries: t.Dict[str, MetricQueryConfig] = {}
        for ref in refs:
            table_name = query.table_name(ref)

            if not query.is_intermediate:
                mart_table = (
                    key_metrics_mart_tables
                    if ref.get("time_aggregation", None) == "over_all_time"
                    else timeseries_mart_tables
                )
                mart_table[ref["entity_type"]].append(table_name)

            additional_macros = [
                metrics_peer_ref,
                metrics_entity_type_col,
                metrics_entity_type_table,
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
                metadata=query._source.metadata,
                incremental=query._source.incremental,
                additional_tags=query._source.additional_tags or [],
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

                if db_name != self.schema:
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
        from metrics_tools.factory.proxy.proxies import (
            aggregate_metadata,
            join_all_of_entity_type,
            map_metadata_to_metric,
        )

        # Generate the models

        for _, query_config, dependencies in self.generate_ordered_queries():
            self.generate_model_for_rendered_query(
                calling_file, query_config, dependencies
            )

        # Join all of the models of the same entity type into the same view model
        override_path = Path(inspect.getfile(join_all_of_entity_type))
        override_module_path = Path(
            os.path.dirname(inspect.getfile(join_all_of_entity_type))
        )

        for entity_type, tables in self._timeseries_marts_tables.items():
            MacroOverridingModel(
                additional_macros=[],
                override_module_path=override_module_path,
                override_path=override_path,
                locals=dict(
                    db=self.schema,
                    tables=tables,
                    columns=list(
                        constants.METRICS_COLUMNS_BY_ENTITY[entity_type].keys()
                    ),
                ),
                name=f"oso.timeseries_metrics_to_{entity_type}",
                is_sql=True,
                kind="VIEW",
                dialect="clickhouse",
                start=self._raw_options["start"],
                columns={
                    k: constants.METRICS_COLUMNS_BY_ENTITY[entity_type][k]
                    for k in filter(
                        lambda col: col not in ["event_source"],
                        constants.METRICS_COLUMNS_BY_ENTITY[entity_type].keys(),
                    )
                },
                enabled=self._raw_options.get("enabled", True),
                tags=[
                    "model_type:view",
                    "model_category:metrics",
                    "model_stage:intermediate",
                    "model_metrics_type:timeseries_union",
                ],
            )(join_all_of_entity_type)

        for entity_type, tables in self._key_metrics_marts_tables.items():
            MacroOverridingModel(
                additional_macros=[],
                override_module_path=override_module_path,
                override_path=override_path,
                locals=dict(
                    db=self.schema,
                    tables=tables,
                    columns=list(
                        constants.METRICS_COLUMNS_BY_ENTITY[entity_type].keys()
                    ),
                ),
                name=f"oso.key_metrics_to_{entity_type}",
                is_sql=True,
                kind="VIEW",
                dialect="clickhouse",
                start="1970-01-01",
                columns={
                    k: constants.METRICS_COLUMNS_BY_ENTITY[entity_type][k]
                    for k in filter(
                        lambda col: col not in ["event_source"],
                        constants.METRICS_COLUMNS_BY_ENTITY[entity_type].keys(),
                    )
                },
                enabled=self._raw_options.get("enabled", True),
                tags=[
                    "model_type:view",
                    "model_category:metrics",
                    "model_stage:intermediate",
                ],
            )(join_all_of_entity_type)

        raw_table_metadata = {
            key: asdict(value.metadata)
            for key, value in self._raw_options.get("metric_queries").items()
            if value.metadata is not None
        }

        transformed_metadata = defaultdict(list)

        for table, metadata in raw_table_metadata.items():
            metadata_tuple = tuple(metadata.items())
            transformed_metadata[metadata_tuple].append(table)

        metadata_depends_on = functools.reduce(
            lambda x, y: x.union({f"oso.metrics_metadata_{ident}" for ident in y}),
            transformed_metadata.values(),
            set(),
        )

        for metric_key, metric_value in self._raw_options.get("metric_queries").items():
            if not metric_value.metadata:
                continue

            MacroOverridingModel(
                additional_macros=[],
                depends_on=[],
                override_module_path=override_module_path,
                override_path=override_path,
                locals={
                    "metric": metric_key,
                    "metadata": asdict(metric_value.metadata),
                },
                name=f"oso.metrics_metadata_{metric_key}",
                is_sql=True,
                kind="FULL",
                dialect="clickhouse",
                columns=constants.METRIC_METADATA_COLUMNS,
                enabled=self._raw_options.get("enabled", True),
                tags=[
                    "model_type:incremental",
                    "model_category:metrics",
                    "model_stage:intermediate",
                    "model_metrics_type:metrics_metadata",
                ],
            )(map_metadata_to_metric)

        MacroOverridingModel(
            additional_macros=[],
            depends_on=metadata_depends_on,
            override_module_path=override_module_path,
            override_path=override_path,
            locals={},
            name="oso.metrics_metadata",
            is_sql=True,
            kind="FULL",
            dialect="clickhouse",
            columns=constants.METRIC_METADATA_COLUMNS,
            enabled=self._raw_options.get("enabled", True),
            tags=[
                "model_type:incremental",
                "model_category:metrics",
                "model_stage:intermediate",
                "model_metrics_type:metrics_metadata",
            ],
        )(aggregate_metadata)

        logger.info("model generation complete")

    def generate_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        query_fns = [
            self.generate_rolling_python_model_for_rendered_query,
            self.generate_time_aggregation_model_for_rendered_query,
            self.generate_point_in_time_model_for_rendered_query,
        ]

        for query_fn in query_fns:
            query_fn(calling_file, query_config, dependencies)

    def generate_rolling_python_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        from metrics_tools.factory.proxy.proxies import generated_rolling_query_proxy

        # if it does not have rolling set, we skip
        # this is because we are calling everything against
        # everything and we delegate to the generator function
        # the choice of what to generate
        ref = query_config["ref"]
        if not ref.get("window"):
            return None

        depends_on = set()
        for dep in dependencies:
            depends_on.add(f"{self.schema}.{dep}")

        query = query_config["query"]

        columns = constants.METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]

        kind_common = {
            "batch_size": ref.get("batch_size", 365),
            "batch_concurrency": 1,
            "lookback": 10,
            "forward_only": True,
        }
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

        # Override the path and module so that sqlmesh generates the
        # proper python_env for the model
        override_path = Path(inspect.getfile(generated_rolling_query_proxy))
        override_module_path = Path(
            os.path.dirname(inspect.getfile(generated_rolling_query_proxy))
        )
        return MacroOverridingModel(
            name=f"{self.schema}.{query_config['table_name']}",
            is_sql=False,
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
            enabled=self._raw_options.get("enabled", True),
            additional_macros=self.generated_model_additional_macros,
            locals=self.serializable_config(query_config),
            override_module_path=override_module_path,
            override_path=override_path,
            tags=[
                "model_type:incremental",
                "model_category:metrics",
                "model_stage:intermediate",
                "model_metrics_type:rolling_window",
                *query_config["additional_tags"],
            ],
        )(generated_rolling_query_proxy)

    def generate_time_aggregation_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        """Generate model for time aggregation models"""
        from metrics_tools.factory.proxy.proxies import generated_query

        # Use a simple python sql model to generate the time_aggregation model
        ref = query_config["ref"]
        if (
            not ref.get("time_aggregation")
            or ref.get("time_aggregation") == "over_all_time"
        ):
            return None

        columns = constants.METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]

        time_aggregation = ref.get("time_aggregation")
        assert time_aggregation in ["daily", "weekly", "monthly"]

        kind_common = {
            "batch_concurrency": 1,
            "forward_only": True,
        }
        kind_options = {"lookback": 10, **kind_common}
        partitioned_by = ("day(metrics_sample_date)",)

        if time_aggregation == "weekly":
            kind_options = {"lookback": 10, **kind_common}
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
        cron = constants.TIME_AGGREGATION_TO_CRON[time_aggregation]

        # Override the path and module so that sqlmesh generates the
        # proper python_env for the model
        override_path = Path(inspect.getfile(generated_query))
        override_module_path = Path(os.path.dirname(inspect.getfile(generated_query)))

        if not query_config["incremental"]:
            kind = {"name": ModelKindName.FULL}
            model_type_tag = "model_type:full"
        else:
            kind = {
                "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                "time_column": "metrics_sample_date",
                **kind_options,
            }
            model_type_tag = "model_type:incremental"

        return MacroOverridingModel(
            name=f"{self.schema}.{query_config['table_name']}",
            kind=kind,
            dialect="clickhouse",
            is_sql=True,
            columns=columns,
            grain=grain,
            cron=cron,
            start=self._raw_options["start"],
            partitioned_by=partitioned_by,
            enabled=self._raw_options.get("enabled", True),
            additional_macros=self.generated_model_additional_macros,
            locals=self.serializable_config(query_config),
            override_module_path=override_module_path,
            override_path=override_path,
            tags=[
                model_type_tag,
                "model_category:metrics",
                "model_stage:intermediate",
                "model_metrics_type:time_aggregation",
                *query_config["additional_tags"],
            ],
        )(generated_query)

    def generate_point_in_time_model_for_rendered_query(
        self,
        calling_file: str,
        query_config: MetricQueryConfig,
        dependencies: t.Set[str],
    ):
        """Generate model for point in time models"""
        from metrics_tools.factory.proxy.proxies import generated_query

        ref = query_config["ref"]
        if ref.get("time_aggregation") != "over_all_time":
            return None

        columns = constants.METRICS_COLUMNS_BY_ENTITY[ref["entity_type"]]
        config = self.serializable_config(query_config)

        grain = [
            "metric",
            f"to_{ref['entity_type']}_id",
            "from_artifact_id",
            "event_source",
            "metrics_sample_date",
        ]

        override_path = Path(inspect.getfile(generated_query))
        override_module_path = Path(os.path.dirname(inspect.getfile(generated_query)))

        return MacroOverridingModel(
            name=f"{self.schema}.{query_config['table_name']}",
            kind=ModelKindName.FULL,
            dialect="clickhouse",
            is_sql=True,
            columns=columns,
            grain=grain,
            start=self._raw_options["start"],
            enabled=self._raw_options.get("enabled", True),
            additional_macros=self.generated_model_additional_macros,
            locals=config,
            override_module_path=override_module_path,
            override_path=override_path,
            tags=[
                "model_type:full",
                "model_category:metrics",
                "model_stage:intermediate",
                "model_metrics_type:point_in_time",
            ],
        )(generated_query)

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
        return [
            metrics_end,
            metrics_start,
            metrics_sample_date,
            metrics_sample_interval_length,
        ]


# Specifically for testing. This is used if the
# `metrics_tools.utils.testing.ENABLE_TIMESERIES_DEBUG` variable is true. This
# is for loading all of the timeseries metrics from inside the oso_sqlmesh
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


# This is to maintain compatibility with the deployed version of sqlmesh models
# We need a way to ensure that changes to generated models are never breaking
# (we will likely need some testing for this)
def generated_query(
    evaluator: MacroEvaluator,
    *args: t.Any,
    **kwargs: t.Any,
):
    """LEGACY VERSION THAT WILL BE DELETED"""
    return parse_one("select 1")


def join_all_of_entity_type(
    evaluator: MacroEvaluator,
    *args: t.Any,
    **kwargs: t.Any,
):
    """LEGACY VERSION THAT WILL BE DELETED"""
    return parse_one("select 1")
