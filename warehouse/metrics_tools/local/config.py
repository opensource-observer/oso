import logging
import typing as t
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


class RowRestriction(BaseModel):
    time_column: str = ""
    # Other expressions that are used in the row restriction. These are joined
    # using `AND`
    wheres: t.List[str] = []

    def as_str(self, start: datetime, end: datetime, dialect: str = "bigquery") -> str:
        where_expressions: t.List[exp.Expression] = []
        if self.time_column:
            where_expressions.append(
                exp.GTE(
                    this=exp.to_column(self.time_column),
                    expression=exp.Literal(
                        this=start.strftime("%Y-%m-%d"), is_string=True
                    ),
                )
            )
            where_expressions.append(
                exp.LT(
                    this=exp.to_column(self.time_column),
                    expression=exp.Literal(
                        this=end.strftime("%Y-%m-%d"), is_string=True
                    ),
                )
            )
        additional_where_expressions = [parse_one(where) for where in self.wheres]
        where_expressions.extend(additional_where_expressions)
        return " AND ".join([ex.sql(dialect=dialect) for ex in where_expressions])

    def has_restriction(self) -> bool:
        return bool(self.time_column or self.wheres)


class TableMappingDestination(BaseModel):
    row_restriction: RowRestriction = Field(default_factory=lambda: RowRestriction())
    table: str = ""

    def has_restriction(self) -> bool:
        if self.row_restriction:
            return self.row_restriction.has_restriction()
        return False


class DestinationLoader(t.Protocol):
    def load_from_bq(
        self,
        config: "Config",
        start: datetime,
        end: datetime,
        source_name: str,
        destination: TableMappingDestination,
    ): ...


class Config(BaseModel):
    table_mapping: t.Dict[str, str | TableMappingDestination]
    max_days: int = 7
    max_results_per_query: int = 0
    project_id: str = "opensource-observer"

    def load_tables_into(self, loader: DestinationLoader):
        start = datetime.now() - timedelta(days=self.max_days)
        end = datetime.now()
        for source_name, destination in self.table_mapping.items():
            if isinstance(destination, str):
                destination = TableMappingDestination(table=destination)
            loader.load_from_bq(self, start, end, source_name, destination)
