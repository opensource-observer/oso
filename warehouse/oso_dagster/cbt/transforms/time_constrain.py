import random
import string
from typing import List, Optional, TypeVar, cast

import arrow
import sqlglot as sql
from sqlglot import expressions as exp
from sqlglot.optimizer.qualify import qualify

from ..context import ContextQuery, DataContext, Transformation
from ..utils import replace_source_tables

T = TypeVar("T")


def time_constrain[T](
    time_column: str,
    start: Optional[arrow.Arrow] = None,
    end: Optional[arrow.Arrow] = None,
) -> Transformation[T]:
    """Transforms any query into a time constrained query for the matching tables"""

    def _transform(query: ContextQuery[T]) -> ContextQuery[T]:
        def _cq(ctx: DataContext[T]) -> exp.Expression:
            expression = query(ctx)
            if not isinstance(expression, exp.Select):
                raise Exception("Can only transform a select statement")
            expression = cast(exp.Select, expression)

            if start:
                expression = expression.where(
                    f"{time_column} >= '{start.format('YYYY-MM-DD')}'"
                )

            if end:
                expression = expression.where(
                    f"{time_column} < '{end.format('YYYY-MM-DD')}'"
                )
            return expression

        return _cq

    return _transform


def _random_suffix():
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(10)
    )


def time_constrain_table[T](
    time_column: str,
    table_name: str,
    start: Optional[arrow.Arrow] = None,
    end: Optional[arrow.Arrow] = None,
) -> Transformation[T]:
    # General strategy is to create a CTE for the table to be constrained and
    # then replace all occurrences of it
    def _transform(query: ContextQuery[T]) -> ContextQuery[T]:
        def _cq(ctx: DataContext[T]):
            expression = query(ctx)

            assert isinstance(expression, exp.Select)

            # Ensure that everything in this query is qualified
            expression = cast(exp.Select, qualify(expression))

            table_to_find = sql.to_table(table_name)
            cte_name = f"generated_{table_to_find.name}_{_random_suffix()}"
            cte_table_reference = sql.to_table(cte_name)

            expression = cast(
                exp.Select,
                expression.transform(
                    replace_source_tables(
                        table_to_find,
                        cte_table_reference,
                    )
                ),
            )

            # Add the cte for the table
            cte_select = sql.select("*").from_(table_to_find)
            cte_select = ctx.transform_query(
                cte_select, [time_constrain(time_column, start=start, end=end)]
            )

            ctes = expression.find(exp.With)
            if ctes:
                original_expressions = cast(List[exp.CTE], ctes.expressions)
                expression = expression.with_(cte_name, as_=cte_select, append=False)
                for e in original_expressions:
                    expression = expression.with_(e.alias, as_=e.this)
            else:
                expression = expression.with_(cte_name, as_=cte_select)

            return expression

        return _cq

    return _transform
