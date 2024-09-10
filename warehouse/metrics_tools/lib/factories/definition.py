import typing as t
import os
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from enum import Enum

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
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
    rolling: t.NotRequired[t.Optional[RollingConfig]]

    # The types of entities to apply this to
    entity_types: t.List[str]


VALID_ENTITY_TYPES = ["artifact", "project", "collection"]


class PeerMetricDependencyRef(t.TypedDict):
    name: str
    entity_type: str
    window: t.NotRequired[t.Optional[int]]
    unit: t.NotRequired[t.Optional[str]]
    rollup: t.NotRequired[t.Optional[str]]


class MetricModelRef(t.TypedDict):
    name: str
    entity_type: str
    window: t.NotRequired[t.Optional[int]]
    unit: t.NotRequired[t.Optional[str]]
    rollup: t.NotRequired[t.Optional[str]]


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
    rollup: t.Optional[str] = None


def to_actual_table_name(
    ref: PeerMetricDependencyRef, peer_table_map: t.Dict[str, str]
):
    ref_table_name = reference_to_str(ref)
    return peer_table_map[ref_table_name]


def reference_to_str(ref: PeerMetricDependencyRef, actual_name: str = ""):
    name = actual_name or ref["name"]
    result = f"{name}_to_{ref['entity_type']}"
    if ref.get("window"):
        result = f"{result}_over_{ref.get('window')}{ref.get('unit')}"
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
    vars: t.Optional[t.Dict[str, ExtraVarType]] = None

    name: t.Optional[str] = None

    dialect: t.Optional[str] = None

    rolling: t.Optional[RollingConfig] = None

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
        if self.rollups and self.rolling:
            raise Exception(
                "Invalid metric query definition. Only one of rollups or trailing_windows can be used"
            )
        if self.rollups is not None and self.rolling is not None:
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


class PeerRefHandler(CustomFuncHandler[PeerMetricDependencyRef]):
    name = "__peer_ref"

    def to_obj(
        self,
        name,
        *,
        entity_type: t.Optional[str] = None,
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        rollup: t.Optional[str] = None,
    ) -> PeerMetricDependencyRef:
        return PeerMetricDependencyRef(
            name=name,
            entity_type=entity_type or "",
            window=window,
            unit=unit,
            rollup=rollup,
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
            if isinstance(table.this, exp.Anonymous):
                anon = table.this
                if anon.this != "__peer_ref":
                    continue
                # Turn the peer ref function into a PeerMetricDependencyRef object
                # send_anonymous_to_callable(
                #     anon,
                # )

            # if table.db is not None:
            #     db = sqlglot.to_identifier(table.db)
            #     table_name = sqlglot.to_identifier(table.this)
            #     if db.this == "peer":
            #         deps.add(table_name.this)
        return deps

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
        if ref["entity_type"] == "artifact":
            return self.generate_artifact_query(
                evaluator,
                ref["name"],
                peer_table_map,
                window=ref.get("window"),
                unit=ref.get("unit"),
                rollup=ref.get("rollup"),
            )
        elif ref["entity_type"] == "project":
            return self.generate_project_query(
                evaluator,
                ref["name"],
                peer_table_map,
                window=ref.get("window"),
                unit=ref.get("unit"),
                rollup=ref.get("rollup"),
            )
        raise Exception("what?")

    def find_all_aggregating_selects(self, expression: exp.Expression):
        selects = expression.find_all(exp.Select)
        for select in selects:
            if select.args.get("group"):
                yield select

    def generate_metrics_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        entity_type: str,
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        rollup: t.Optional[str] = None,
    ):
        context = self.expression_context()

        extra_vars: t.Dict[str, ExtraVarType] = {
            "entity_type": entity_type,
        }
        if window:
            extra_vars["rolling_window"] = window
        if unit:
            extra_vars["unit"] = unit
        if rollup:
            extra_vars["rollup"] = rollup

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
        rollup: t.Optional[str] = None,
    ):
        metrics_query = self.generate_metrics_query(
            evaluator,
            name,
            peer_table_map,
            "artifact",
            window,
            unit,
            rollup,
        )

        top_level_select = exp.select(
            "metrics_bucket_date as bucket_day",
            "to_artifact_id as to_artifact_id",
            "from_artifact_id as from_artifact_id",
            "event_source as event_source",
            "metric as metric",
            "CAST(amount AS Float64) as amount",
        ).from_("metrics_query")

        top_level_select = top_level_select.with_("metrics_query", as_=metrics_query)
        return top_level_select

    def generate_project_query(
        self,
        evaluator: MacroEvaluator,
        name: str,
        peer_table_map: t.Dict[str, str],
        window: t.Optional[int] = None,
        unit: t.Optional[str] = None,
        rollup: t.Optional[str] = None,
    ):
        metrics_query = self.generate_metrics_query(
            evaluator,
            name,
            peer_table_map,
            "artifact",
            window,
            unit,
            rollup,
        )

        metrics_query = qualify(metrics_query)

        # Find all of the queries that group by the `to_artifact_id`
        for select in self.find_all_aggregating_selects(metrics_query):
            for i in range(len(select.expressions)):
                ex = select.expressions[i]
                if not isinstance(ex, exp.Alias):
                    continue
                # If to_artifact_id is being aggregated then it's time to rewrite
                if isinstance(ex.this, exp.Column) and isinstance(
                    ex.this.this, exp.Identifier
                ):
                    if ex.this.this.this == "to_artifact_id":
                        print("!!!!!!!!!!!!!!!!!!!!")
                        updated_select = select.copy()
                        current_from = t.cast(exp.From, updated_select.args.get("from"))
                        assert isinstance(current_from.this, exp.Table)
                        current_table = current_from.this
                        current_alias = current_table.alias

                        # Add a join to this select
                        updated_select = updated_select.join(
                            "artifacts_by_project_v1",
                            on=f"{current_alias}.to_artifact_id = artifacts_by_project_v1.artifact_id",
                            join_type="inner",
                        )
                        # replace the select and the grouping with the project id in the joined table
                        to_artifact_id_col_sel = t.cast(
                            exp.Alias, updated_select.expressions[i]
                        )
                        current_to_artifact_id_col = t.cast(
                            exp.Column, to_artifact_id_col_sel.this
                        )
                        new_to_project_id_col = exp.to_column(
                            "artifacts_by_project_v1.project_id", quoted=True
                        )

                        to_artifact_id_col_sel.replace(
                            exp.alias_(
                                new_to_project_id_col,
                                alias=exp.to_identifier("to_project_id", quoted=True),
                            )
                        )

                        group = t.cast(exp.Group, updated_select.args.get("group"))
                        for group_idx in range(len(group.expressions)):
                            group_col = t.cast(exp.Column, group.expressions[group_idx])
                            if group_col == current_to_artifact_id_col:
                                group_col.replace(new_to_project_id_col)

                        print("REPLACING________________")
                        print(updated_select.sql())

                        select.replace(updated_select)

        top_level_select = exp.select(
            "metrics_bucket_date as bucket_day",
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
        rollup: t.Optional[str] = None,
    ):
        metrics_query = self.generate_metrics_query(
            evaluator,
            name,
            peer_table_map,
            "artifact",
            window,
            unit,
            rollup,
        )

        top_level_select = exp.select(
            "metrics_bucket_date as bucket_day",
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


class TimeseriesMetricsOptions(t.TypedDict):
    model_prefix: str
    metric_queries: t.Dict[str, MetricQueryDef]
    default_dialect: t.NotRequired[str]
    model_options: t.NotRequired[t.Dict[str, t.Any]]


class GeneratedArtifactConfig(t.TypedDict):
    query_reference_name: str
    query_def_as_input: MetricQueryInput
    default_dialect: str
    peer_table_map: t.Dict[str, str]
    ref: PeerMetricDependencyRef


def generated_entity(
    evaluator: MacroEvaluator,
    query_reference_name: str,
    query_def_as_input: MetricQueryInput,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
    ref: PeerMetricDependencyRef,
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
    print(e.sql())
    if not e:
        raise Exception("failed to generate query ref")
    return e


def generated_project(
    evaluator: MacroEvaluator,
    query_reference_name: str,
    query_def_as_input: MetricQueryInput,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
    ref: PeerMetricDependencyRef,
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


def generated_collection(
    evaluator: MacroEvaluator,
    query_reference_name: str,
    query_def_as_input: MetricQueryInput,
    default_dialect: str,
    peer_table_map: t.Dict[str, str],
    ref: PeerMetricDependencyRef,
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
