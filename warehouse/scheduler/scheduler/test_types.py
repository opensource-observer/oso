
import pytest
from scheduler.types import Model


def compare_sql_queries(query1: str, query2: str) -> bool:
    """Compares two SQL queries for structural equality, ignoring formatting differences."""
    from sqlglot import parse_one
    from sqlglot.optimizer.qualify_tables import qualify_tables

    tree1 = qualify_tables(parse_one(query1), dialect="trino")
    tree2 = qualify_tables(parse_one(query2), dialect="trino")
    return tree1 == tree2


@pytest.fixture
def model(request) -> Model:
    code = request.param
    return Model(
        code=code,
        id="model_123",
        name="test_model",
        org_id="org_123",
        org_name="test_org",
        dataset_name="test_dataset",
        dataset_id="ds_123",
        language="sql",
        dialect="trino",
    )


@pytest.mark.parametrize(
    "model,expected_query",
    [
        (
            """SELECT ARRAY[1, 1.2, 4][2]""",
            """SELECT ARRAY[1, 1.2, 4][2]""",
        ),
    ],
    indirect=["model"],
)
@pytest.mark.asyncio
async def test_model_parse_correctly(
    model: Model,
    expected_query: str,
):
    query = model.query
    resolved_query = await model.resolve_query([])
    compare_sql_queries(query.sql("trino"), expected_query)
    compare_sql_queries(resolved_query.sql("trino"), expected_query)
