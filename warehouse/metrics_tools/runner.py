"""Run metrics queries for a given boundary"""

import abc
import asyncio
import logging
import typing as t
from datetime import datetime

import arrow
import duckdb
import pandas as pd
from metrics_tools.definition import MetricModelDefinition, RollingCronOptions
from metrics_tools.intermediate import run_macro_evaluator
from metrics_tools.macros import (
    metrics_end,
    metrics_sample_date,
    metrics_sample_interval_length,
    metrics_start,
)
from metrics_tools.models.tools import create_unregistered_macro_registry
from metrics_tools.utils.glot import str_or_expressions
from sqlglot import exp
from sqlmesh import EngineAdapter
from sqlmesh.core.config import DuckDBConnectionConfig
from sqlmesh.core.context import ExecutionContext
from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter
from sqlmesh.core.macros import MacroRegistry, RuntimeStage

logger = logging.getLogger(__name__)


def generate_duckdb_create_table(df: pd.DataFrame, table_name: str) -> str:
    # Map Pandas dtypes to DuckDB types
    dtype_mapping = {
        "int64": "BIGINT",
        "int32": "INTEGER",
        "float64": "DOUBLE",
        "float32": "FLOAT",
        "bool": "BOOLEAN",
        "object": "TEXT",
        "datetime64[ns]": "TIMESTAMP",
        "datetime64[us]": "TIMESTAMP",
        "timedelta64[ns]": "INTERVAL",
    }

    # Start the CREATE TABLE statement
    create_statement = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"

    # Generate column definitions
    column_definitions = []
    for col in df.columns:
        col_type = dtype_mapping.get(
            str(df[col].dtype), "TEXT"
        )  # Default to TEXT for unknown types
        column_definitions.append(f"    {col} {col_type}")

    # Join the column definitions and finish the statement
    create_statement += ",\n".join(column_definitions)
    create_statement += "\n);"

    return create_statement


class RunnerEngine(abc.ABC):
    def execute_df(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("execute_df not implemented")

    def execute(self, query: str):
        raise NotImplementedError("execute_df not implemented")


class ExistingDuckDBConnectionConfig(DuckDBConnectionConfig):
    def __init__(self, conn: duckdb.DuckDBPyConnection, *args, **kwargs):
        self._existing_connection = conn
        super().__init__(*args, **kwargs)

    @property
    def _connection_factory(self) -> t.Callable:
        return lambda: self._existing_connection


class FakeEngineAdapter(EngineAdapter):
    """This needs some work"""

    def __init__(self, dialect: str):
        self.dialect = dialect


ROLLING_CRON_TO_ARROW_UNIT: t.Dict[
    RollingCronOptions, t.Literal["day", "month", "year", "week"]
] = {
    "@daily": "day",
    "@weekly": "week",
    "@monthly": "month",
    "@yearly": "year",
}


def render_metrics_query(
    query: str | t.List[exp.Expression] | exp.Expression,
    ref: MetricModelDefinition,
    variables: t.Optional[t.Dict[str, t.Any]] = None,
    engine_adapter: t.Optional[EngineAdapter] = None,
    additional_macros: t.Optional[MacroRegistry] = None,
    runtime_stage: RuntimeStage = RuntimeStage.EVALUATING,
    dialect: str = "duckdb",
):
    variables = variables or {}

    time_aggregation = ref.get("time_aggregation")
    rolling_window = ref.get("window")
    rolling_unit = ref.get("unit")
    if time_aggregation:
        variables["time_aggregation"] = time_aggregation
    if rolling_window and rolling_unit:
        variables["rolling_window"] = rolling_window
        variables["rolling_unit"] = rolling_unit

    variables.setdefault("start_ds", datetime(1970, 1, 1).strftime("%Y-%m-%d"))
    variables.setdefault("end_ds", datetime.now().strftime("%Y-%m-%d"))

    additional_macros = create_unregistered_macro_registry(
        [
            metrics_end,
            metrics_start,
            metrics_sample_date,
            metrics_sample_interval_length,
        ]
    )
    evaluated_query = run_macro_evaluator(
        query,
        additional_macros=additional_macros,
        variables=variables,
        engine_adapter=engine_adapter,
        runtime_stage=runtime_stage,
        dialect=dialect,
    )
    return evaluated_query


class MetricsRunner:
    @classmethod
    def create_duckdb_execution_context(
        cls,
        conn: duckdb.DuckDBPyConnection,
        query: str | t.List[exp.Expression],
        ref: MetricModelDefinition,
        locals: t.Optional[t.Dict[str, t.Any]],
    ):
        def connection_factory():
            return conn

        engine_adapter = DuckDBEngineAdapter(connection_factory)
        context = ExecutionContext(engine_adapter, {})
        return cls(context, str_or_expressions(query), ref, locals)

    @classmethod
    def from_engine_adapter(
        cls,
        engine_adapter: EngineAdapter,
        query: str | t.List[exp.Expression],
        ref: MetricModelDefinition,
        locals: t.Optional[t.Dict[str, t.Any]],
    ):
        context = ExecutionContext(engine_adapter, {})
        return cls(context, str_or_expressions(query), ref, locals)

    @classmethod
    def from_sqlmesh_context(
        cls,
        context: ExecutionContext,
        query: str | t.List[exp.Expression],
        ref: MetricModelDefinition,
        locals: t.Optional[t.Dict[str, t.Any]] = None,
    ):
        return cls(context, str_or_expressions(query), ref, locals)

    def __init__(
        self,
        context: ExecutionContext,
        query: t.List[exp.Expression],
        ref: MetricModelDefinition,
        locals: t.Optional[t.Dict[str, t.Any]] = None,
    ):
        self._context = context
        self._query = query
        self._ref = ref
        self._locals = locals or {}

    def run(self, start: datetime, end: datetime):
        """Run metrics for a given period and return the results as pandas dataframes"""
        if self._ref.get("time_aggregation"):
            return self.run_time_aggregation(start, end)
        else:
            return self.run_rolling(start, end)

    def run_time_aggregation(self, start: datetime, end: datetime):
        rendered_query = self.render_query(start, end)
        logger.debug("executing time aggregation", extra={"query": rendered_query})
        return self._context.engine_adapter.fetchdf(rendered_query)

    def run_rolling(self, start: datetime, end: datetime):
        df: pd.DataFrame = pd.DataFrame()
        logger.debug(
            f"run_rolling[{self._ref['name']}]: called with start={start} and end={end}"
        )
        count = 0
        total_rows = 0
        for rendered_query in self.render_rolling_queries(start, end):
            count += 1
            logger.debug(
                f"run_rolling[{self._ref['name']}]: executing rolling window: {rendered_query}",
                extra={"query": rendered_query},
            )
            day_result = self._context.engine_adapter.fetchdf(rendered_query)
            day_rows = len(day_result)
            total_rows += day_rows
            logger.debug(
                f"run_rolling[{self._ref['name']}]: rolling window period resulted in {day_rows} rows"
            )
            df = pd.concat([df, day_result])
        logger.debug(f"run_rolling[{self._ref['name']}]: total rows {total_rows}")

        return df

    def render_query(self, start: datetime, end: datetime) -> str:
        variables: t.Dict[str, t.Any] = {
            "start_ds": start.strftime("%Y-%m-%d"),
            "end_ds": end.strftime("%Y-%m-%d"),
        }
        variables.update(self._locals)
        logger.debug(f"start_ds={variables['start_ds']} end_ds={variables['end_ds']}")

        evaluated_query = render_metrics_query(
            self._query,
            self._ref,
            engine_adapter=self._context.engine_adapter,
            variables=variables,
            additional_macros=None,
            runtime_stage=RuntimeStage.EVALUATING,
        )
        # additional_macros = create_unregistered_macro_registry(
        #     [
        #         metrics_end,
        #         metrics_start,
        #         metrics_sample_date,
        #         metrics_sample_interval_length,
        #     ]
        # )
        # evaluated_query = run_macro_evaluator(
        #     self._query,
        #     additional_macros=additional_macros,
        #     variables=variables,
        #     engine_adapter=self._context.engine_adapter,
        #     runtime_stage=RuntimeStage.EVALUATING,
        # )
        rendered_parts = list(
            map(
                lambda a: a.sql(dialect=self._context.engine_adapter.dialect),
                evaluated_query,
            )
        )
        return "\n".join(rendered_parts)

    def render_rolling_queries(self, start: datetime, end: datetime) -> t.Iterator[str]:
        # Given a rolling input render all the rolling queries
        logger.debug(f"render_rolling_queries called with start={start} and end={end}")
        for day in self.iter_query_days(start, end):
            rendered_query = self.render_query(day, day)
            yield rendered_query

    def iter_query_days(self, start: datetime, end: datetime):
        cron = self._ref.get("cron")
        assert cron is not None, "cron is required for rolling queries"
        arrow_interval = ROLLING_CRON_TO_ARROW_UNIT[cron]
        if arrow_interval == "week":
            # We want to start weeks on sunday so we need to adjust the start time to the next sunday
            start_arrow = arrow.get(start)
            day_of_week = start_arrow.weekday()
            if day_of_week != 6:
                start = start_arrow.shift(days=6 - day_of_week).datetime
        for day in arrow.Arrow.range(arrow_interval, arrow.get(start), arrow.get(end)):
            yield day.datetime

    async def render_rolling_queries_async(self, start: datetime, end: datetime):
        logger.debug(
            f"render_rolling_queries_async called with start={start} and end={end}"
        )
        for day in self.iter_query_days(start, end):
            rendered_query = await asyncio.to_thread(self.render_query, day, day)
            yield rendered_query

    def commit(self, start: datetime, end: datetime, destination: str):
        """Like run but commits the result to the database"""
        try:
            result = self.run(start, end)
        except:
            logger.error(
                "Running query failed",
                extra={"query": self._query[0].sql(dialect="duckdb", pretty=True)},
            )
            raise

        create_table = generate_duckdb_create_table(result, destination)

        logger.debug("creating duckdb table")
        self._context.engine_adapter.execute(create_table)

        logger.debug("inserting results from the run")
        self._context.engine_adapter.insert_append(destination, result)
        return result
