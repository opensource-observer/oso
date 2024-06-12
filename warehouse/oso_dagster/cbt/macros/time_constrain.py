from typing import Optional, cast

import arrow
import sqlglot as sql
from sqlglot import expressions as exp
from ..context import DataContext, ContextQuery


def time_constrain(
    time_column: str,
    start: Optional[arrow.Arrow] = None,
    end: Optional[arrow.Arrow] = None,
    table: str = "",
) -> ContextQuery:
    """Transforms any query into a time constrained query"""

    def _transform(query: ContextQuery) -> ContextQuery:
        def _cq(ctx: DataContext) -> exp.Expression:
            expression = query(ctx)
            if type(expression) != exp.Select:
                raise Exception("Can only transform a select statement")
            expression = cast(exp.Select, expression)
            print(list(expression.find_all(exp.Select)))

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
