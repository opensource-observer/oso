import typing as t
import os
import uuid
from dataclasses import dataclass
from contextlib import contextmanager
from enum import Enum

import sqlglot
from sqlglot import exp
from sqlmesh.core.model import model
from sqlmesh.core.macros import MacroEvaluator
from oso_dagster.cbt.utils import replace_source_tables

CURR_DIR = os.path.dirname(__file__)
QUERIES_DIR = os.path.abspath(os.path.join("../../oso_metrics"))


@dataclass
class RollingWindow:
    trailing_days: int


class TimeseriesBucket(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


VarType = exp.Expression | str | int | float


@dataclass
class MetricQuery:
    # The relative path to the query in `oso_metrics`
    ref: str

    # Additional vars
    vars: t.Dict[str, VarType | t.Callable[[], VarType]]

    def load_exp(self) -> t.List[exp.Expression]:
        """Loads the queries sql file as a sqlglot expression"""
        return t.cast(
            t.List[exp.Expression],
            filter(
                lambda a: a is not None,
                sqlglot.parse(open(os.path.join(QUERIES_DIR, self.ref)).read()),
            ),
        )

    @contextmanager
    def query_vars(self, evaluator: MacroEvaluator):
        before = evaluator.locals.copy()
        evaluator.locals.update(self.vars)
        try:
            yield
        finally:
            evaluator.locals = before


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
        if len(find_select_expressions(self._expressions)) > 1:
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

    def evaluate(self, evaluator: MacroEvaluator) -> exp.Query:
        select_to_return: t.Optional[exp.Query] = None
        with self._source.query_vars(evaluator):
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
                if db.this == "__peer__":
                    deps.add(table_name.this)
        return deps


def find_select_expressions(expressions: t.List[exp.Expression]):
    return list(filter(lambda a: isinstance(a, exp.Query), expressions))


class DailyTimeseriesRollingWindowOptions(t.TypedDict):
    model_name: str
    metric_queries: t.Dict[str, MetricQuery]
    trailing_days: int


def daily_timeseries_rolling_window_model(options: DailyTimeseriesRollingWindowOptions):
    @model(name=options["model_name"], is_sql=True)
    def generated_model(evaluator: MacroEvaluator):
        # Given a set of rolling metrics together. This will also ensure that
        # all of the rolling windows are identical.

        # Combine all of the queries
        # together into a single query. Once all of the queries have been
        # completed.
        cte_suffix = uuid.uuid4().hex
        subqueries: t.Dict[str, Subquery] = {}
        for query_name, query in options["metric_queries"].items():
            subquery = subqueries[query_name] = Subquery.load(
                name=query_name, source=query
            )

        union_cte: t.Optional[exp.Query] = None
        top_level_select = exp.select(
            "bucket_day", "to_artifact_id", "from_artifact_id", "event_source", "metric"
        ).from_(f"all_{cte_suffix}")

        for name, subquery in subqueries.items():
            # Validate the given dependencies
            deps = subquery.dependencies
            for dep in deps:
                if dep not in name:
                    raise Exception("Missing dependency for metric query {name}")
                # Replace all the references to that table and replace it with a CTE reference
                replace_dep = replace_source_tables(
                    sqlglot.to_table(f"__peer__.{dep}"),
                    sqlglot.to_table(f"{dep}_{cte_suffix}"),
                )
                subquery.transform_expressions(replace_dep)

            # Evaluate the expressions in the subquery
            cte_name = f"{name}_{cte_suffix}"
            evaluated = subquery.evaluate(evaluator)
            top_level_select = top_level_select.with_(evaluated, as_=cte_name)
            unionable_select = sqlglot.select("*").from_(cte_name)
            if not union_cte:
                union_cte = unionable_select
            else:
                union_cte.union(unionable_select)

        if not union_cte:
            raise Exception("no queries generated from the evaluated queries")
        top_level_select.with_(union_cte, as_=f"all_{cte_suffix}")
        return top_level_select
