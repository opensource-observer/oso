import logging
import re
import typing as t

from oso_agent.util.parse import postprocess, remove_distinct, replace_cur_year
import sqlglot
from sqlglot import expressions as exp

logger = logging.getLogger(__name__)
_DIALECT = "trino"

def clean_query_for_eval(query: str, keep_distinct: bool = True) -> str:
    """Sanitize a sql query for evaluation"""
    cleaned_query = sanitize_query_from_agent(query)
    cleaned_query = postprocess(cleaned_query)

    # Is this actually needed? It seems to replace current year with 2020
    cleaned_query = replace_cur_year(cleaned_query)

    if not keep_distinct:
        cleaned_query = remove_distinct(cleaned_query)
    return cleaned_query
    

def sanitize_query_from_agent(query: str, input_dialect: str = "trino") -> str:
    """
    Remove the dialect prefix from an agent SQL response.
    Handles both 'trino\nSELECT ...' and 'trino SELECT ...' cases.
    """
    query = query.strip()
    pattern = rf"^{input_dialect}\s*[\n ]+"
    query = re.sub(pattern, "", query, flags=re.IGNORECASE)
    return query


def load_expected_sql_answer(expected: dict[str, t.Any]) -> str:
    """Load the expected answer from the example."""
    expected_answer = expected.get("answer")
    if not expected_answer:
        logger.warning("No expected answer provided, defaulting to 'SELECT 1'")
        expected_answer = "SELECT 1"
    return expected_answer

ExampleQueryType = t.Literal[
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

def determine_query_type(query: str, dialect: str = _DIALECT) -> t.List:
    try:
        tree = sqlglot.parse_one(query, dialect=dialect)
        types: t.List[ExampleQueryType] = []

        AGG_NODES = (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)
        if any(tree.find(node_cls) for node_cls in AGG_NODES):
            types.append("aggregation")
            
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
    
    except Exception:
        return []


def determine_sql_models_used(query: str, dialect: str = _DIALECT) -> t.List:
    try:
        tree = sqlglot.parse_one(query, dialect=dialect)
        tables = list(set([tbl.name for tbl in tree.find_all(exp.Table)]))
        return tables
    except Exception:
        return []
