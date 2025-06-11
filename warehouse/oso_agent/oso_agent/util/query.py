from typing import List, Literal

import sqlglot
from sqlglot import expressions as exp

_DIALECT = "trino"

def sanitize_query_from_agent(query: str, input_dialect: str = "trino") -> str:
    """Sanitize a sql query from an agent response. This is to remove any
    unwanted characters or formatting that sometimes seem to appear in agent
    responses."""

    line_split = [ line.lower() for line in query.strip().split('\n')]
    if input_dialect.lower() in line_split:
        if line_split[0] == input_dialect.lower():
            query = "\n".join(line_split[1:])
    return query

ExampleQueryType = Literal[
    "aggregation",     
    "filter",         
    "join",            
    "group_by",        
    "order_by",        
    "window_function",
    "time_series",    
    "limit",         
    "union",           
    "case_when",      
    "array",           
    "cte",             
    "other"            
]

def determine_query_type(query: str, dialect: str = _DIALECT) -> List[ExampleQueryType]:
    tree = sqlglot.parse_one(query, dialect=dialect)

    types: List[ExampleQueryType] = []

    AGG_FUNCS = {"count", "sum", "avg", "min", "max"}
    for func in tree.find_all(exp.Func):
        if func.name.lower() in AGG_FUNCS:
            types.append("aggregation")
            break

    if tree.find(exp.Where):
        types.append("filter")

    if tree.find(exp.Join):
        types.append("join")

    if tree.find(exp.Group):
        types.append("group_by")

    if tree.find(exp.Order):
        types.append("order_by")

    if tree.find(exp.Limit):
        types.append("limit")

    if tree.find(exp.With):
        types.append("cte")

    if tree.find(exp.Union):
        types.append("union")

    if tree.find(exp.Window):
        types.append("window_function")

    if tree.find(exp.Case):
        types.append("case_when")

    if tree.find(exp.ArrayAgg) or tree.find(exp.Array):
        types.append("array")

    time_funcs = {
        "date", "date_add", "date_diff", "date_trunc", "extract",
        "time", "timestamp", "to_unixtime", "from_unixtime", "interval"
    }
    for func in tree.find_all(exp.Func):
        if func.name.lower() in time_funcs:
            types.append("time_series")
            break

    if not types:
        types.append("other")

    return types


def determine_sql_models_used(query: str, dialect: str = _DIALECT) -> List[str]:
    tree = sqlglot.parse_one(query, dialect=dialect)
    tables = list(set([tbl.name for tbl in tree.find_all(exp.Table)]))
    return tables