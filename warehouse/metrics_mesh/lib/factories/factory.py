import typing as t
import os
import uuid
from dataclasses import dataclass
from contextlib import contextmanager
from enum import Enum

import sqlglot
from sqlglot import exp
from sqlmesh.core.model import model, ModelKindName
from sqlmesh.core.macros import MacroEvaluator
from oso_dagster.cbt.utils import replace_source_tables

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join(CURR_DIR, "../../oso_metrics"))

type ExtraVarType = str | int | float


@dataclass
class RollingWindow:
    trailing_days: int


class TimeseriesBucket(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class MetricQueryInput(t.TypedDict):
    ref: str
    # Additional vars
    vars: t.Dict[str, ExtraVarType]
    name: t.NotRequired[str]


@dataclass(kw_only=True)
class MetricQuery:
    # The relative path to the query in `oso_metrics`
    ref: str

    # Additional vars
    vars: t.Dict[str, ExtraVarType]

    name: t.Optional[str] = None

    def load_exp(self) -> t.List[exp.Expression]:
        """Loads the queries sql file as a sqlglot expression"""
        raw_sql = open(os.path.join(QUERIES_DIR, self.ref)).read()
        return t.cast(
            t.List[exp.Expression],
            list(
                filter(
                    lambda a: a is not None,
                    sqlglot.parse(raw_sql),
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
        evaluator.locals.update(self.vars)
        if extra_vars:
            evaluator.locals.update(extra_vars)
        try:
            yield
        finally:
            evaluator.locals = before

    @classmethod
    def from_input(cls, input: MetricQueryInput):
        return MetricQuery(**input)

    def to_input(self) -> MetricQueryInput:
        input = MetricQueryInput(vars=self.vars, ref=self.ref)
        if self.name:
            input["name"] = self.name
        return input


class Subquery:
    @classmethod
    def load(cls, *, name: str, source: MetricQuery):
        subquery = cls(name, source, source.load_exp())
        subquery.validate()
        return subquery

    def __init__(
        self,
        name: str,
        source: MetricQuery,
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
    def dependencies(self) -> t.Set[str]:
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


def find_select_expressions(expressions: t.List[exp.Expression]):
    return list(filter(lambda a: isinstance(a, exp.Query), expressions))


class DailyTimeseriesRollingWindowOptions(t.TypedDict):
    model_name: str
    metric_queries: t.Dict[str, MetricQuery]
    trailing_days: int
    model_options: t.NotRequired[t.Dict[str, t.Any]]


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
            "bucket_day": "Date",
            "event_source": "String",
            "to_artifact_id": "String",
            "from_artifact_id": "String",
            "metric": "String",
            "amount": "Int64",
        },
        **(raw_options.get("model_options", {})),
    )
    def generated_model(evaluator: MacroEvaluator):
        # Given a set of rolling metrics together. This will also ensure that
        # all of the rolling windows are identical.

        # Combine all of the queries
        # together into a single query. Once all of the queries have been
        # completed.
        cte_suffix = uuid.uuid4().hex

        subqueries: t.Dict[str, Subquery] = {}
        for query_name, query_input in metric_queries.items():
            query = MetricQuery.from_input(query_input)
            subquery = subqueries[query_name] = Subquery.load(
                name=query_name, source=query
            )

        union_cte: t.Optional[exp.Query] = None
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
            deps = subquery.dependencies
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
            unionable_select = sqlglot.select("*").from_(cte_name)
            if not union_cte:
                union_cte = unionable_select
            else:
                union_cte = union_cte.union(unionable_select, distinct=False)

        if not union_cte:
            raise Exception("no queries generated from the evaluated queries")
        top_level_select = top_level_select.with_(f"all_{cte_suffix}", union_cte)
        return top_level_select
