import typing as t
import os
import uuid
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from enum import Enum

import sqlglot
from sqlglot import exp
from sqlmesh.core.model import model, ModelKindName
from sqlmesh.core.macros import MacroEvaluator
from oso_dagster.cbt.utils import replace_source_tables

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../oso_metrics"))

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]


@dataclass
class RollingWindow:
    trailing_days: int


class TimeseriesBucket(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


DEFAULT_ENTITY_TYPES = ["artifact", "project", "collection"]


class MetricQueryInput(t.TypedDict):
    # The relative path to the file in the `oso_metrics` directory
    ref: str

    # The dialect that's used to parse the sql
    dialect: t.NotRequired[t.Optional[str]]

    # Additional vars for the metric
    vars: t.NotRequired[t.Optional[t.Dict[str, ExtraVarType]]]

    # This is the name used for the metric. By default this name is derived from
    # the top level configuration used in the configuration factory that uses
    # this input.
    name: t.NotRequired[t.Optional[str]]

    # Setting rollups aggregates a metric over a specific time period. This is
    # similar to trailing windows but the meaning is semantically differnt in
    # that the aggregation is assumed to be an additive aggregation. So if the
    # buckets of daily and monthly are used it is assumed you can add the daily
    # aggregation within that month and get the value. At this bucket
    # aggregations cannot be combined with trailing windows.
    #
    # Available options are daily, weekly, monthly, yearly
    rollups: t.NotRequired[t.Optional[t.List[str]]]

    # If windows is specified then this metric is calculated within the given
    # windows of trailing days. Cannot be set if buckets is set
    trailing_windows: t.NotRequired[t.Optional[t.List[int]]]

    # The types of entities to apply this to
    entity_types: t.List[str]


VALID_ENTITY_TYPES = ["artifact", "project", "collection"]


class PeerMetricDependencyRef(t.TypedDict):
    name: str
    entity_type: str
    trailing_window: t.NotRequired[t.Optional[int]]
    rollup: t.NotRequired[t.Optional[str]]


def reference_to_str(ref: PeerMetricDependencyRef, actual_name: str = ""):
    name = actual_name or ref["name"]
    result = f"{name}_to_{ref['entity_type']}"
    if ref.get("trailing_window"):
        result = f"{result}_over_{ref.get('trailing_window')}days"
    if ref.get("rollup"):
        result = f"{result}_{ref.get('rollup')}"
    return result


def assert_allowed_items_in_list[T](to_validate: t.List[T], allowed_items: t.List[T]):
    for item in to_validate:
        assert item in allowed_items, "List contains invalid items"


@dataclass(kw_only=True)
class MetricQueryDef:
    # The relative path to the query in `oso_metrics`
    ref: str

    entity_types: t.Optional[t.List[str]] = None

    # Additional vars
    vars: t.Optional[t.Dict[str, ExtraVarType]]

    name: t.Optional[str] = None

    dialect: t.Optional[str] = None

    trailing_windows: t.Optional[t.List[int]] = None

    rollups: t.Optional[t.List[str]] = None

    def load_exp(self, default_dialect: str) -> t.List[exp.Expression]:
        """Loads the queries sql file as a sqlglot expression"""
        raw_sql = open(os.path.join(QUERIES_DIR, self.ref)).read()

        dialect = self.dialect or default_dialect
        return t.cast(
            t.List[exp.Expression],
            list(
                filter(
                    lambda a: a is not None,
                    sqlglot.parse(raw_sql, dialect=dialect),
                )
            ),
        )

    @contextmanager
    def query_vars(
        self,
        evaluator: MacroEvaluator,
        extra_vars: t.Optional[t.Dict[str, ExtraVarType]] = None,
    ):
        before = evaluator.locals.copy()
        evaluator.locals.update(self.vars or {})
        if extra_vars:
            evaluator.locals.update(extra_vars)
        try:
            yield
        finally:
            evaluator.locals = before

    def validate(self):
        if not self.entity_types:
            self.entity_types = DEFAULT_ENTITY_TYPES
        # Validate the given input
        if self.rollups and self.trailing_windows:
            raise Exception(
                "Invalid metric query definition. Only one of rollups or trailing_windows can be used"
            )
        if self.rollups is not None and self.trailing_windows is not None:
            raise Exception(
                "Invalid metric query definition. One of rollups or trailing_windows must be set"
            )
        assert_allowed_items_in_list(self.entity_types, VALID_ENTITY_TYPES)
        assert_allowed_items_in_list(
            self.rollups or [], ["daily", "weekly", "monthly", "yearly"]
        )

    @classmethod
    def from_input(cls, input: MetricQueryInput):
        return MetricQueryDef(**input)

    def to_input(self) -> MetricQueryInput:
        return t.cast(MetricQueryInput, asdict(self))

    def resolve_table_name(
        self, prefix: str, peer_name: str, entity_type: str, suffix: str = ""
    ):
        assert entity_type in (self.entity_types or DEFAULT_ENTITY_TYPES)
        name = self.name or peer_name
        model_name = f"{prefix}_{name}_to_{entity_type}"
        if suffix:
            model_name = f"{model_name}_{suffix}"
        return model_name


class MetricQueryContext:
    def __init__(self, source: MetricQueryDef, expressions: t.List[exp.Expression]):
        self._expressions = expressions
        self._source = source

    def transform_expressions(
        self, transformation: t.Callable[[exp.Expression], exp.Expression]
    ):
        self._expressions = list(
            map(lambda a: a.transform(transformation), self._expressions)
        )

    def evaluate(
        self,
        name: str,
        evaluator: MacroEvaluator,
        extra_vars: t.Optional[t.Dict[str, ExtraVarType]] = None,
    ) -> exp.Query:
        select_to_return: t.Optional[exp.Query] = None
        if not extra_vars:
            extra_vars = {}
        extra_vars["metric_name"] = self._source.name or name

        with self._source.query_vars(evaluator, extra_vars=extra_vars):
            for expression in self._expressions:
                transformed = evaluator.transform(expression)
                if isinstance(transformed, exp.Query):
                    select_to_return = transformed
            if not select_to_return:
                raise Exception(
                    f"No select could be evaluated from query {self._source.ref}"
                )
        return select_to_return


class MetricQuery:
    @classmethod
    def load(cls, *, name: str, default_dialect: str, source: MetricQueryDef):
        subquery = cls(name, source, source.load_exp(default_dialect))
        subquery.validate()
        return subquery

    def __init__(
        self,
        name: str,
        source: MetricQueryDef,
        expressions: t.List[exp.Expression],
    ):
        self._name = name
        self._source = source
        self._expressions = expressions

    def validate(self):
        queries = find_select_expressions(self._expressions)
        if len(queries) != 1:
            raise Exception(
                f"There must only be a single query expression in metrics query {self._source.ref}"
            )

    @property
    def query_expression(self) -> exp.Query:
        return t.cast(exp.Query, find_select_expressions(self._expressions)[0])

    def expression_context(self):
        return MetricQueryContext(self._source, self._expressions[:])

    def transform_expressions(
        self, transformation: t.Callable[[exp.Expression], exp.Expression]
    ):
        self._expressions = list(
            map(lambda a: a.transform(transformation), self._expressions)
        )

    def evaluate(
        self,
        evaluator: MacroEvaluator,
        extra_vars: t.Optional[t.Dict[str, ExtraVarType]] = None,
    ) -> exp.Query:
        select_to_return: t.Optional[exp.Query] = None
        if not extra_vars:
            extra_vars = {}
        extra_vars["metric_name"] = self._source.name or self._name

        with self._source.query_vars(evaluator, extra_vars=extra_vars):
            for expression in self._expressions:
                transformed = evaluator.transform(expression)
                if isinstance(transformed, exp.Query):
                    select_to_return = transformed
            if not select_to_return:
                raise Exception(
                    f"No select could be evaluated from query {self._source.ref}"
                )
        return select_to_return

    @property
    def reference_name(self):
        return self._name

    def table_name(self, ref: PeerMetricDependencyRef):
        name = self._source.name or self._name
        return reference_to_str(ref, name)

    @property
    def peer_dependencies(self) -> t.Set[str]:
        # Find all dependencies
        table_expressions: t.List[exp.Table] = t.cast(
            t.List[exp.Table], self.query_expression.find_all(exp.Table)
        )

        deps: t.Set[str] = set()

        for table in table_expressions:
            if table.db is not None:
                db = sqlglot.to_identifier(table.db)
                table_name = sqlglot.to_identifier(table.this)
                if db.this == "peer":
                    deps.add(table_name.this)
        return deps

    @property
    def dependency_refs(self):
        """
        Generates a list of refs required for this specific model
        """
        deps = self.peer_dependencies
        # Explode the query peer dependencies into the expected generated models
        # and the resultant dependency references
        refs: t.List[PeerMetricDependencyRef] = []
        for dep in deps:
            refs.extend(self.generate_dependency_refs_for_name(dep))
        return refs

    def generate_dependency_refs_for_name(self, name: str):
        refs: t.List[PeerMetricDependencyRef] = []
        for entity in self._source.entity_types or DEFAULT_ENTITY_TYPES:
            for window in self._source.trailing_windows or []:
                refs.append(
                    PeerMetricDependencyRef(
                        name=name,
                        entity_type=entity,
                        trailing_window=window,
                    )
                )
            for rollup in self._source.rollups or []:
                refs.append(
                    PeerMetricDependencyRef(
                        name=name,
                        entity_type=entity,
                        rollup=rollup,
                    )
                )
        return refs

    @property
    def provided_dependency_refs(self):
        return self.generate_dependency_refs_for_name(self.reference_name)

    def generate_query_ref(
        self,
        ref: PeerMetricDependencyRef,
        evaluator: MacroEvaluator,
        peer_table_map: t.Dict[str, str],
    ):
        print("ref")
        print(ref)
        if ref["entity_type"] == "artifact":
            print("RIGHT HERE???")
            return self.generate_artifact_query(
                evaluator,
                ref["name"],
                peer_table_map,
                trailing_window=ref.get("trailing_window"),
                rollup=ref.get("rollup"),
            )

    def generate_artifact_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        trailing_window: t.Optional[int] = None,
        rollup: t.Optional[str] = None,
    ):
        context = self.expression_context()

        # run the query and pass in the specific vars it needs
        peer_dependencies = self.peer_dependencies
        for dep in peer_dependencies:
            ref = PeerMetricDependencyRef(
                name=dep,
                entity_type="artifact",
                trailing_window=trailing_window,
                rollup=rollup,
            )
            ref_str = reference_to_str(ref)
            actual_table = peer_table_map[ref_str]
            replace_dep = replace_source_tables(
                sqlglot.to_table(f"peer.{dep}"),
                sqlglot.to_table(f"metrics.{actual_table}"),
            )
            context.transform_expressions(replace_dep)
        extra_vars: t.Dict[str, ExtraVarType] = {"entity_type": "artifact"}
        if trailing_window:
            extra_vars["trailing_days"] = trailing_window
        if rollup:
            extra_vars["rollup"] = rollup

        top_level_select = exp.select(
            "metrics_bucket_date as bucket_day",
            "to_artifact_id as to_artifact_id",
            "from_artifact_id as from_artifact_id",
            "event_source as event_source",
            "metric as metric",
            "CAST(amount AS Float64) as amount",
        ).from_("metrics_query")
        metrics_query = context.evaluate(
            name,
            evaluator,
            extra_vars,
        )
        top_level_select = top_level_select.with_("metrics_query", as_=metrics_query)
        print(top_level_select.sql(dialect="clickhouse"))
        return top_level_select

    def generate_project_query(
        self,
        evaluator: MacroEvaluator,
        default_dialect: str,
        name: str,
        trailing_window: t.Optional[int] = None,
        rollup: t.Optional[str] = None,
    ):
        pass

    def generate_collection_query(
        self,
        evaluator: MacroEvaluator,
        default_dialect: str,
        name: str,
        trailing_window: t.Optional[int] = None,
        rollup: t.Optional[str] = None,
    ):
        pass


def generate_models_from_query(
    query: MetricQuery, default_dialect: str, peer_table_map: t.Dict[str, str]
):
    # Turn the source into a dict so it can be used in the sqlmesh context
    query_def_as_input = query._source.to_input()
    query_reference_name = query.reference_name
    refs = query.provided_dependency_refs
    for ref in refs:
        if ref["entity_type"] == "artifact":

            @model(
                name=f"metrics.{query.table_name(ref)}",
                kind={
                    "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
                    "time_column": "bucket_day",
                    "batch_size": 1,
                },
                is_sql=True,
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
            )
            def _generated_to_artifact(evaluator: MacroEvaluator, **kwargs):
                query_def = MetricQueryDef.from_input(query_def_as_input)
                inner_query = MetricQuery.load(
                    name=query_reference_name,
                    default_dialect=default_dialect,
                    source=query_def,
                )
                e = inner_query.generate_query_ref(
                    ref,
                    evaluator,
                    peer_table_map=peer_table_map,
                )
                if not e:
                    raise Exception("shit")
                print(e.sql())
                return e

        if ref["entity_type"] == "project":
            pass

        if ref["entity_type"] == "collection":
            pass


# def generate_models_for_metric_query(name: str, query_def: MetricQueryDef):
#     tables: t.Dict[str, str] = {}
#     query_def_as_dict = query_def.to_input()
#     if "artifact" in query_def.entity_types:

#         @model(
#             name=query_def.resolve_table_name(name, "artifact"),


def find_select_expressions(expressions: t.List[exp.Expression]):
    return list(filter(lambda a: isinstance(a, exp.Query), expressions))


class DailyTimeseriesRollingWindowOptions(t.TypedDict):
    model_name: str
    metric_queries: t.Dict[str, MetricQueryDef]
    trailing_days: int
    model_options: t.NotRequired[t.Dict[str, t.Any]]


# def generate_models_for_metric_query(name: str, query_def: MetricQueryDef):
#     tables: t.Dict[str, str] = {}
#     query_def_as_dict = query_def.to_input()
#     if "artifact" in query_def.entity_types:

#         @model(
#             name=query_def.resolve_table_name(name, "artifact"),
#             is_sql=True,
#             kind={
#                 "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
#                 "time_column": "bucket_day",
#                 "batch_size": 1,
#             },
#             dialect="clickhouse",
#             columns={
#                 "bucket_day": exp.DataType.build("DATE", dialect="clickhouse"),
#                 "event_source": exp.DataType.build("String", dialect="clickhouse"),
#                 "to_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
#                 "from_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
#                 "metric": exp.DataType.build("String", dialect="clickhouse"),
#                 "amount": exp.DataType.build("Float64", dialect="clickhouse"),
#             },
#             grain=["metric", "to_artifact_id", "from_artifact_id", "bucket_day"],
#         )
#         def _generated_to_artifact_models():
#             pass

#     if "project" in query_def.entity_types:
#         pass

#     if "collection" in query_def.entity_types:
#         pass


class TimeseriesMetricsOptions(t.TypedDict):
    model_prefix: str
    metric_queries: t.Dict[str, MetricQueryDef]
    default_dialect: t.NotRequired[str]
    model_options: t.NotRequired[t.Dict[str, t.Any]]


def timeseries_metrics(
    **raw_options: t.Unpack[TimeseriesMetricsOptions],
):
    metrics_queries = [
        MetricQuery.load(
            name=name,
            default_dialect=raw_options.get("default_dialect", "clickhouse"),
            source=query_def,
        )
        for name, query_def in raw_options["metric_queries"].items()
    ]

    # Build the dependency graph of all the metrics queries
    dependencies: t.Dict[str, t.List[PeerMetricDependencyRef]] = {}
    peer_table_map: t.Dict[str, str] = {}
    for query in metrics_queries:
        dependencies[query.reference_name] = query.dependency_refs

        provided_refs = query.provided_dependency_refs
        for ref in provided_refs:
            peer_table_map[reference_to_str(ref)] = query.table_name(ref)

    # Validate the graph
    for dep, refs in dependencies.items():
        for ref in refs:
            if reference_to_str(ref) not in peer_table_map:
                raise Exception(
                    f"Missing a reference to a necessary table for {dep} with {ref}"
                )

    print("HI HI H2")
    # Generate the models
    for query in metrics_queries:
        print("HI HI HI")
        generate_models_from_query(
            query,
            default_dialect=raw_options.get("default_dialect", "clickhouse"),
            peer_table_map=peer_table_map,
        )

    # Join all of the models of the same entity type into the same


def daily_timeseries_rolling_window_model(
    **raw_options: t.Unpack[DailyTimeseriesRollingWindowOptions],
):
    # We need to turn the options into something we can have easily pickled due
    # to some sqlmesh execution environment management that I don't yet fully
    # understand.
    metric_queries = {
        key: obj.to_input() for key, obj in raw_options["metric_queries"].items()
    }
    model_name = raw_options["model_name"]
    trailing_days = raw_options["trailing_days"]

    @model(
        name=model_name,
        is_sql=True,
        kind={
            "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
            "time_column": "bucket_day",
            "batch_size": 1,
        },
        dialect="clickhouse",
        columns={
            "bucket_day": exp.DataType.build("DATE", dialect="clickhouse"),
            "event_source": exp.DataType.build("String", dialect="clickhouse"),
            "to_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
            "from_artifact_id": exp.DataType.build("String", dialect="clickhouse"),
            "metric": exp.DataType.build("String", dialect="clickhouse"),
            "amount": exp.DataType.build("Float64", dialect="clickhouse"),
        },
        grain=["metric", "to_artifact_id", "from_artifact_id", "bucket_day"],
        **(raw_options.get("model_options", {})),
    )
    def generated_model(evaluator: MacroEvaluator):
        # Given a set of rolling metrics together. This will also ensure that
        # all of the rolling windows are identical.

        # Combine all of the queries
        # together into a single query. Once all of the queries have been
        # completed.
        cte_suffix = uuid.uuid4().hex

        subqueries: t.Dict[str, MetricQuery] = {}
        for query_name, query_input in metric_queries.items():
            query = MetricQueryDef.from_input(query_input)
            subquery = subqueries[query_name] = MetricQuery.load(
                name=query_name, default_dialect="clickhouse", source=query
            )

        union_cte: t.Optional[exp.Query] = None

        cte_column_select = [
            "metrics_bucket_date as bucket_day",
            "to_artifact_id as to_artifact_id",
            "from_artifact_id as from_artifact_id",
            "event_source as event_source",
            "metric as metric",
            "CAST(amount AS Float64) as amount",
        ]

        top_level_select = exp.select(
            "bucket_day",
            "to_artifact_id",
            "from_artifact_id",
            "event_source",
            "metric",
            "amount",
        ).from_(f"all_{cte_suffix}")

        for name, subquery in subqueries.items():
            # Validate the given dependencies
            deps = subquery.peer_dependencies
            for dep in deps:
                if dep not in subqueries:
                    raise Exception(f"Missing dependency {dep} for metric query {name}")
                # Replace all the references to that table and replace it with a CTE reference
                replace_dep = replace_source_tables(
                    sqlglot.to_table(f"peer.{dep}"),
                    sqlglot.to_table(f"{dep}_{cte_suffix}"),
                )
                subquery.transform_expressions(replace_dep)

            # Evaluate the expressions in the subquery
            cte_name = f"{name}_{cte_suffix}"
            evaluated = subquery.evaluate(
                evaluator, extra_vars=dict(trailing_days=trailing_days)
            )
            top_level_select = top_level_select.with_(cte_name, as_=evaluated)
            unionable_select = sqlglot.select(*cte_column_select).from_(cte_name)
            if not union_cte:
                union_cte = unionable_select
            else:
                union_cte = union_cte.union(unionable_select, distinct=False)

        if not union_cte:
            raise Exception("no queries generated from the evaluated queries")
        top_level_select = top_level_select.with_(f"all_{cte_suffix}", union_cte)
        return top_level_select
