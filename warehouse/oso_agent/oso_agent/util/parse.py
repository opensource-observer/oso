import re

from sqlglot import expressions as exp
from sqlglot import parse_one

_DIALECT = "trino"


def replace_cur_year(query: str) -> str:
    return re.sub(
        r"YEAR\s*\(\s*CURDATE\s*\(\s*\)\s*\)\s*", "2020", query, flags=re.IGNORECASE
    )


# postprocess the model predictions to avoid execution errors
# e.g. removing spaces between ">" and "="
def postprocess(query: str) -> str:
    query = query.replace('> =', '>=').replace('< =', '<=').replace('! =', '!=')
    return query


def remove_distinct(sql: str, dialect: str = _DIALECT) -> str:
    try:
        tree = parse_one(sql, read=dialect)
        
        for select in tree.find_all(exp.Select):
            select.set("distinct", False)
        
        return tree.sql(dialect=dialect)
    
    except Exception:
        return ""