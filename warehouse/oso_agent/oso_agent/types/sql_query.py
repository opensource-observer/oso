from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, ValidationError
from sqlglot import parse_one

DEFAULT_SQL_DIALECT = "trino"

def is_valid_sql(text: str, dialect: str = DEFAULT_SQL_DIALECT) -> str:
    try:
        parse_one(text, dialect=dialect)
        return text
    except Exception as e:
        raise ValidationError(
            f"Invalid SQL query: {text}. Error: {str(e)}"
        )

class SqlQuery(BaseModel):
    query: Annotated[str, Field(description="A valid SQL query that will be executed on a query engine."), AfterValidator(is_valid_sql)]