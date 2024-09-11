import typing as t
import os
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from enum import Enum

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlmesh.utils.date import TimeLike
from sqlmesh.core.macros import MacroEvaluator
from metrics_tools.dialect.translate import (
    CustomFuncHandler,
    CustomFuncRegistry,
)
from metrics_tools.evaluator import FunctionsTransformer

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(
    os.path.join(CURR_DIR, "../../../metrics_mesh/oso_metrics")
)

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]


class RollingConfig(t.TypedDict):
    windows: t.List[int]
    unit: str
    cron: str


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

    # Setting time_aggregations aggregates a metric over a specific time period.
    # This is similar to trailing windows but the meaning is semantically
    # differnt in that the aggregation is assumed to be an additive aggregation.
    # So if the buckets of daily and monthly are used it is assumed you can add
    # the daily aggregation within that month and get the value. At this bucket
    # aggregations cannot be combined with trailing windows.
    #
    # Available options are daily, weekly, monthly, yearly
    time_aggregations: t.NotRequired[t.Optional[t.List[str]]]

    # If windows is specified then this metric is calculated within the given
    # windows of trailing days. Cannot be set if buckets is set
    rolling: t.NotRequired[t.Optional[RollingConfig]]

    # The types of entities to apply this to
    entity_types: t.List[str]


VALID_ENTITY_TYPES = ["artifact", "project", "collection"]


class PeerMetricDependencyRef(t.TypedDict):
    name: str
    entity_type: str
    window: t.NotRequired[t.Optional[int]]
    unit: t.NotRequired[t.Optional[str]]
    time_aggregation: t.NotRequired[t.Optional[str]]


class MetricModelRef(t.TypedDict):
    name: str
    entity_type: str
    window: t.NotRequired[t.Optional[int]]
    unit: t.NotRequired[t.Optional[str]]
    time_aggregation: t.NotRequired[t.Optional[str]]


def model_meta_matches_peer_dependency(meta: MetricModelRef, dep: MetricModelRef):
    if meta["name"] != dep["name"]:
        return False
    if isinstance(dep["entity_type"], list):
        if not meta["entity_type"] not in dep["entity_type"]:
            return False
    else:
        if meta["entity_type"] != dep["entity_type"]:
            if dep["entity_type"] != "*":
                return False
    dep_window = dep.get("window")
    if dep_window:
        if isinstance(dep_window, list):
            pass


@dataclass(kw_only=True)
class PeerMetricDependencyDataClass:
    name: str
    entity_type: str

    window: t.Optional[int] = None
    unit: t.Optional[str] = None
    time_aggregation: t.Optional[str] = None


def to_actual_table_name(
    ref: PeerMetricDependencyRef, peer_table_map: t.Dict[str, str]
):
    ref_table_name = reference_to_str(ref)
    return peer_table_map[ref_table_name]


def reference_to_str(ref: PeerMetricDependencyRef, actual_name: str = ""):
    name = actual_name or ref["name"]
    result = f"{name}_to_{ref['entity_type']}"
    suffix= time_suffix(ref.get('time_aggregation'), ref.get('window'), ref.get('unit'))
    return f"{result}_{suffix}"


def time_suffix(time_aggregation: t.Optional[str], window: t.Optional[int | str], unit: t.Optional[str]):
    if window:
        return f"over_{window}_{unit}"
    if time_aggregation:
        return time_aggregation


def assert_allowed_items_in_list[T](to_validate: t.List[T], allowed_items: t.List[T]):
    for item in to_validate:
        assert item in allowed_items, "List contains invalid items"


@dataclass(kw_only=True)
class MetricQueryDef:
    # The relative path to the query in `oso_metrics`
    ref: str

    entity_types: t.Optional[t.List[str]] = None

    # Additional vars
    vars: t.Optional[t.Dict[str, ExtraVarType]] = None

    name: t.Optional[str] = None

    dialect: t.Optional[str] = None

    rolling: t.Optional[RollingConfig] = None

    time_aggregations: t.Optional[t.List[str]] = None

    @property
    def raw_sql(self):
        return open(os.path.join(QUERIES_DIR, self.ref)).read()

    def load_exp(self, default_dialect: str) -> t.List[exp.Expression]:
        """Loads the queries sql file as a sqlglot expression"""
        raw_sql = self.raw_sql

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
        if self.time_aggregations and self.rolling:
            raise Exception(
                "Invalid metric query definition. Only one of time_aggregations or trailing_windows can be used"
            )
        if self.time_aggregations is not None and self.rolling is not None:
            raise Exception(
                "Invalid metric query definition. One of time_aggregations or trailing_windows must be set"
            )
        assert_allowed_items_in_list(self.entity_types, VALID_ENTITY_TYPES)
        assert_allowed_items_in_list(
            self.time_aggregations or [], ["daily", "weekly", "monthly", "yearly"]
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
    

def exp_literal_to_py_literal(glot_literal: exp.Expression) -> t.Any:
    # Don't error by default let it pass
    if not isinstance(glot_literal, exp.Literal):
        return glot_literal
    return glot_literal.this
    

class PeerRefHandler(CustomFuncHandler[PeerMetricDependencyRef]):
    name = "metrics_peer_ref"

    def to_obj(
        self,
        name,
        *,
        entity_type: t.Optional[exp.Expression] = None,
        window: t.Optional[exp.Expression] = None,
        unit: t.Optional[exp.Expression] = None,
        time_aggregation: t.Optional[exp.Expression] = None,
    ) -> PeerMetricDependencyRef:
        entity_type_val = t.cast(str, exp_literal_to_py_literal(entity_type)) if entity_type else "" 
        window_val = int(exp_literal_to_py_literal(window)) if window else None
        unit_val = t.cast(str, exp_literal_to_py_literal(unit)) if unit else None
        time_aggregation_val = t.cast(str, exp_literal_to_py_literal(time_aggregation)) if time_aggregation else None
        return PeerMetricDependencyRef(
            name=name,
            entity_type=entity_type_val,
            window=window_val,
            unit=unit_val,
            time_aggregation=time_aggregation_val,
        )

    def transform(
        self,
        evaluator: MacroEvaluator,
        context: t.Dict[str, t.Any],
        obj: PeerMetricDependencyRef,
    ) -> exp.Expression:
        if not obj.get("entity_type"):
            obj["entity_type"] = context["entity_type"]
        peer_table_map = context["peer_table_map"]
        return sqlglot.to_table(f"metrics.{to_actual_table_name(obj, peer_table_map)}")



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

    def prepend_expression(self, expression: exp.Expression):
        # Useful for setting a local macro definition
        self._expressions = [expression] + self._expressions

    def append_expression(self, expression: exp.Expression):
        self._expressions = [expression] + self._expressions

    def evaluate(
        self,
        name: str,
        evaluator: MacroEvaluator,
        extra_vars: t.Optional[t.Dict[str, ExtraVarType]] = None,
    ) -> exp.Query:
        select_to_return: t.Optional[exp.Query] = None
        if not extra_vars:
            extra_vars = {}
        extra_vars["generated_metric_name"] = self._source.name or name

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

    @property
    def reference_name(self):
        return self._name

    def table_name(self, ref: PeerMetricDependencyRef):
        name = self._source.name or self._name
        return reference_to_str(ref, name)

    def generate_dependency_refs_for_name(self, name: str):
        refs: t.List[PeerMetricDependencyRef] = []
        for entity in self._source.entity_types or DEFAULT_ENTITY_TYPES:
            if self._source.rolling:
                for window in self._source.rolling["windows"]:
                    refs.append(
                        PeerMetricDependencyRef(
                            name=name,
                            entity_type=entity,
                            window=window,
                            unit=self._source.rolling.get('unit'),
                        )
                    )
            for time_aggregation in self._source.time_aggregations or []:
                refs.append(
                    PeerMetricDependencyRef(
                        name=name,
                        entity_type=entity,
                        time_aggregation=time_aggregation,
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
        if ref["entity_type"] == "artifact":
            return self.generate_artifact_query(
                evaluator,
                ref["name"],
                peer_table_map,
                window=ref.get("window"),
                unit=ref.get("unit"),
                time_aggregation=ref.get("time_aggregation"),
            )
        elif ref["entity_type"] == "project":
            return self.generate_project_query(
                evaluator,
                ref["name"],
                peer_table_map,
                window=ref.get("window"),
                unit=ref.get("unit"),
                time_aggregation=ref.get("time_aggregation"),
            )
        elif ref["entity_type"] == "collection":
            return self.generate_collection_query(
                evaluator,
                ref["name"],
                peer_table_map,
                window=ref.get("window"),
                unit=ref.get("unit"),
                time_aggregation=ref.get("time_aggregation"),
            )
        raise Exception(f"Invalid entity_type {ref["entity_type"]}")

    def generate_metrics_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        entity_type: str,
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        time_aggregation: t.Optional[str] = None,
    ):
        context = self.expression_context()

        extra_vars: t.Dict[str, ExtraVarType] = {
            "entity_type": entity_type,
        }
        if window:
            extra_vars["rolling_window"] = window
        if unit:
            extra_vars["rolling_unit"] = unit
        if time_aggregation:
            extra_vars["time_aggregation"] = time_aggregation

        metrics_query = context.evaluate(
            name,
            evaluator,
            extra_vars,
        )
        # Rewrite all of the table peer references. We do this last so that all
        # macros are resolved when rewriting the anonymous functions
        peer_handler = PeerRefHandler()
        registry = CustomFuncRegistry()
        registry.register(peer_handler)
        transformer = FunctionsTransformer(
            registry,
            evaluator,
            context={
                "peer_table_map": peer_table_map,
                "entity_type": entity_type,
            },
        )
        return transformer.transform(metrics_query)

    def generate_artifact_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        time_aggregation: t.Optional[str] = None,
    ):
        metrics_query = self.generate_metrics_query(
            evaluator,
            name,
            peer_table_map,
            "artifact",
            window,
            unit,
            time_aggregation,
        )

        top_level_select = exp.select(
            "metrics_sample_date as metrics_sample_date",
            "to_artifact_id as to_artifact_id",
            "from_artifact_id as from_artifact_id",
            "event_source as event_source",
            "metric as metric",
            "CAST(amount AS Float64) as amount",
        ).from_("metrics_query")

        top_level_select = top_level_select.with_("metrics_query", as_=metrics_query)
        return top_level_select

    def artifact_to_upstream_entity_transform(
        self,
        entity_type: str,
    ) -> t.Callable[[exp.Expression], exp.Expression | None]:
        def _transform(node: exp.Expression):
            if not isinstance(node, exp.Select):
                return node
            select = node

            # Check if this using the timeseries source tables as a join or the from
            is_using_timeseries_source = False
            for table in select.find_all(exp.Table):
                if table.this.this in ['events_daily_to_artifact']:
                    is_using_timeseries_source = True
            if not is_using_timeseries_source:
                return node

            for i in range(len(select.expressions)):
                ex = select.expressions[i]
                if not isinstance(ex, exp.Alias):
                    continue
                
                # If to_artifact_id is being aggregated then it's time to rewrite
                if isinstance(ex.this, exp.Column) and isinstance(
                    ex.this.this, exp.Identifier
                ):
                    if ex.this.this.this == "to_artifact_id":
                        updated_select = select.copy()
                        current_from = t.cast(exp.From, updated_select.args.get("from"))
                        assert isinstance(current_from.this, exp.Table)
                        current_table = current_from.this
                        current_alias = current_table.alias

                        # Add a join to this select
                        updated_select = updated_select.join(
                            "sources.artifacts_by_project_v1",
                            on=f"{current_alias}.to_artifact_id = artifacts_by_project_v1.artifact_id",
                            join_type="inner",
                        )

                        new_to_entity_id_col = exp.to_column(
                            "artifacts_by_project_v1.project_id", quoted=True
                        )
                        new_to_entity_alias = exp.to_identifier(
                            "to_project_id", quoted=True
                        )

                        if entity_type == "collection":
                            updated_select = updated_select.join(
                                "sources.projects_by_collection_v1",
                                on="artifacts_by_project_v1.project_id = projects_by_collection_v1.project_id",
                                join_type="inner"
                            )

                            new_to_entity_id_col = exp.to_column(
                                "projects_by_collection_v1.collection_id", quoted=True
                            )
                            new_to_entity_alias = exp.to_identifier(
                                "to_collection_id", quoted=True
                            )

                        # replace the select and the grouping with the project id in the joined table
                        to_artifact_id_col_sel = t.cast(
                            exp.Alias, updated_select.expressions[i]
                        )
                        current_to_artifact_id_col = t.cast(
                            exp.Column, to_artifact_id_col_sel.this
                        )

                        to_artifact_id_col_sel.replace(
                            exp.alias_(
                                new_to_entity_id_col,
                                alias=new_to_entity_alias,
                            )
                        )

                        group = t.cast(exp.Group, updated_select.args.get("group"))
                        for group_idx in range(len(group.expressions)):
                            group_col = t.cast(exp.Column, group.expressions[group_idx])
                            if group_col == current_to_artifact_id_col:
                                group_col.replace(new_to_entity_id_col)

                        return updated_select
            # If nothing happens in the for loop then we didn't find the kind of
            # expected select statement
            return node

        return _transform

    def transform_aggregating_selects(
        self,
        expression: exp.Expression,
        cb: t.Callable[[exp.Expression], exp.Expression | None],
    ):
        return expression.transform(cb)

    def generate_project_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        time_aggregation: t.Optional[str] = None,
    ):
        metrics_query = self.generate_metrics_query(
            evaluator,
            name,
            peer_table_map,
            "project",
            window,
            unit,
            time_aggregation,
        )

        metrics_query = qualify(metrics_query)

        metrics_query = self.transform_aggregating_selects(
            metrics_query, self.artifact_to_upstream_entity_transform("project")
        )

        top_level_select = exp.select(
            "metrics_sample_date as metrics_sample_date",
            "to_project_id as to_project_id",
            "from_artifact_id as from_artifact_id",
            "event_source as event_source",
            "metric as metric",
            "CAST(amount AS Float64) as amount",
        ).from_("metrics_query")

        top_level_select = top_level_select.with_("metrics_query", as_=metrics_query)
        return top_level_select

    def generate_collection_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        time_aggregation: t.Optional[str] = None,
    ):
        metrics_query = self.generate_metrics_query(
            evaluator,
            name,
            peer_table_map,
            "collection",
            window,
            unit,
            time_aggregation,
        )

        metrics_query = qualify(metrics_query)

        metrics_query = self.transform_aggregating_selects(
            metrics_query, self.artifact_to_upstream_entity_transform("collection")
        )

        top_level_select = exp.select(
            "metrics_sample_date as metrics_sample_date",
            "to_collection_id as to_collection_id",
            "from_artifact_id as from_artifact_id",
            "event_source as event_source",
            "metric as metric",
            "CAST(amount AS Float64) as amount",
        ).from_("metrics_query")

        top_level_select = top_level_select.with_("metrics_query", as_=metrics_query)
        return top_level_select


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


def join_all_of_entity_type(evaluator: MacroEvaluator, *, db: str, tables: t.List[str], columns: t.List[str]):
    query = exp.select(*columns).from_(sqlglot.to_table(f"{db}.{tables[0]}"))
    for table in tables[1:]:
        query.union(exp.select(*columns).from_(sqlglot.to_table(f"{db}.{table}")), distinct=False)
    return query


class TimeseriesMetricsOptions(t.TypedDict):
    model_prefix: str
    metric_queries: t.Dict[str, MetricQueryDef]
    default_dialect: t.NotRequired[str]
    model_options: t.NotRequired[t.Dict[str, t.Any]]
    start: TimeLike
    timeseries_sources: t.NotRequired[t.Optional[t.List[str]]]


class GeneratedArtifactConfig(t.TypedDict):
    query_reference_name: str
    query_def_as_input: MetricQueryInput
    default_dialect: str
    peer_table_map: t.Dict[str, str]
    ref: PeerMetricDependencyRef
    timeseries_sources: t.List[str]


def generated_entity(
    evaluator: MacroEvaluator,
    query_reference_name: str,
    query_def_as_input: MetricQueryInput,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
    ref: PeerMetricDependencyRef,
    timeseries_sources: t.List[str],
):
    query_def = MetricQueryDef.from_input(query_def_as_input)
    query = MetricQuery.load(
        name=query_reference_name,
        default_dialect=default_dialect,
        source=query_def,
    )
    e = query.generate_query_ref(
        ref,
        evaluator,
        peer_table_map=peer_table_map,
    )
    if not e:
        raise Exception("failed to generate query ref")
    return e
