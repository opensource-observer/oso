import os
import typing as t
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import Enum

import sqlglot
from sqlglot import exp
from sqlmesh.core.macros import MacroEvaluator
from sqlmesh.utils.date import TimeLike

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../oso_sqlmesh/oso_metrics"))

type ExtraVarBaseType = str | int | float
type ExtraVarType = ExtraVarBaseType | t.List[ExtraVarBaseType]

RollingCronOptions = t.Literal["@daily", "@weekly", "@monthly", "@yearly"]


class RollingConfig(t.TypedDict):
    windows: t.List[int]
    unit: str
    cron: RollingCronOptions

    # How many days do we process at once. This is useful to set for very large
    # datasets but will default to a year if not set.
    model_batch_size: t.NotRequired[int]

    # The number of required slots for a given model. This is also very useful
    # for large datasets
    slots: t.NotRequired[int]


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
    cron: t.NotRequired[RollingCronOptions]
    batch_size: t.NotRequired[int]
    slots: t.NotRequired[int]


class MetricModelRef(t.TypedDict):
    name: str
    entity_type: str
    window: t.NotRequired[t.Optional[int]]
    unit: t.NotRequired[t.Optional[str]]
    time_aggregation: t.NotRequired[t.Optional[str]]


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
    suffix = time_suffix(
        ref.get("time_aggregation"), ref.get("window"), ref.get("unit")
    )
    return f"{result}_{suffix}"


def time_suffix(
    time_aggregation: t.Optional[str],
    window: t.Optional[int | str],
    unit: t.Optional[str],
):
    if window:
        return f"over_{window}_{unit}_window"
    if time_aggregation:
        return time_aggregation


def assert_allowed_items_in_list[T](to_validate: t.List[T], allowed_items: t.List[T]):
    for item in to_validate:
        assert item in allowed_items, "List contains invalid items"


@dataclass(kw_only=True)
class MetricMetadata:
    description: str
    display_name: str


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

    over_all_time: t.Optional[bool] = False

    is_intermediate: bool = False

    enabled: bool = True

    use_python_model: bool = True

    metadata: t.Optional[MetricMetadata] = None

    def raw_sql(self, queries_dir: str):
        return open(os.path.join(queries_dir, self.ref)).read()

    def load_exp(
        self, queries_dir: str, default_dialect: str
    ) -> t.List[exp.Expression]:
        """Loads the queries sql file as a sqlglot expression"""
        raw_sql = self.raw_sql(queries_dir)

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
    def load(
        cls,
        *,
        name: str,
        default_dialect: str,
        source: MetricQueryDef,
        queries_dir: str,
    ):
        subquery = cls(name, source, source.load_exp(queries_dir, default_dialect))
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
        queries = find_query_expressions(self._expressions)
        if len(queries) != 1:
            raise Exception(
                f"There must only be a single query expression in metrics query {self._source.ref}"
            )

    @property
    def use_python_model(self):
        return self._source.use_python_model

    @property
    def query_expression(self) -> exp.Query:
        return t.cast(exp.Query, find_query_expressions(self._expressions)[0])

    def expression_context(self):
        return MetricQueryContext(self._source, self._expressions[:])

    @property
    def reference_name(self):
        return self._name

    @property
    def vars(self):
        return self._source.vars or {}

    def table_name(self, ref: PeerMetricDependencyRef):
        name = self._source.name or self._name
        return reference_to_str(ref, name)

    def dependencies(
        self, ref: PeerMetricDependencyRef, peer_table_map: t.Dict[str, str]
    ):
        dependencies: t.Set[str] = set()

        for expression in self._expressions:
            anonymous_expressions = expression.find_all(exp.Anonymous)
            for anonymous in anonymous_expressions:
                if anonymous.this == "metrics_peer_ref":
                    dep_name = anonymous.expressions[0].sql()
                    dependencies = dependencies.union(
                        set(
                            filter(
                                lambda a: dep_name in a,
                                peer_table_map.keys(),
                            )
                        )
                    )
        return list(dependencies)

    def generate_dependency_refs_for_name(self, name: str):
        refs: t.List[PeerMetricDependencyRef] = []
        for entity in self._source.entity_types or DEFAULT_ENTITY_TYPES:
            if self._source.rolling:
                for window in self._source.rolling["windows"]:
                    ref = PeerMetricDependencyRef(
                        name=name,
                        entity_type=entity,
                        window=window,
                        unit=self._source.rolling.get("unit"),
                        cron=self._source.rolling.get("cron"),
                    )
                    model_batch_size = self._source.rolling.get("model_batch_size")
                    slots = self._source.rolling.get("slots")
                    if model_batch_size:
                        ref["batch_size"] = model_batch_size
                    if slots:
                        ref["slots"] = slots
                    refs.append(ref)
            for time_aggregation in self._source.time_aggregations or []:
                refs.append(
                    PeerMetricDependencyRef(
                        name=name,
                        entity_type=entity,
                        time_aggregation=time_aggregation,
                    )
                )
            # if we actually enabled over all time, we'll compute that as well
            if self._source.over_all_time:
                refs.append(
                    PeerMetricDependencyRef(
                        name=name,
                        entity_type=entity,
                        time_aggregation="over_all_time",
                    )
                )
        return refs

    @property
    def is_intermediate(self):
        return self._source.is_intermediate

    @property
    def provided_dependency_refs(self):
        return self.generate_dependency_refs_for_name(self.reference_name)


def find_query_expressions(expressions: t.List[exp.Expression]):
    return list(filter(lambda a: isinstance(a, exp.Query), expressions))


class DailyTimeseriesRollingWindowOptions(t.TypedDict):
    model_name: str
    metric_queries: t.Dict[str, MetricQueryDef]
    trailing_days: int
    model_options: t.NotRequired[t.Dict[str, t.Any]]


class TimeseriesMetricsOptions(t.TypedDict):
    model_prefix: str
    catalog: str
    metric_queries: t.Dict[str, MetricQueryDef]
    default_dialect: t.NotRequired[str]
    start: TimeLike
    timeseries_sources: t.NotRequired[t.List[str]]
    queries_dir: t.NotRequired[str]
    enabled: t.NotRequired[bool]
