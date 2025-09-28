import pytest
from oso_agent.eval.text2sql.evals import (
    oso_tables_match,
    results_exact_match,
    results_similarity_score,
    sql_command_types_match,
    sql_execution_success,
    sql_syntax_validation,
)

from ..types.eval import ExampleResult

VERBOSE = True


def vprint(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


# Dummy stub for local testing
class ResultFixtures:
    def fake_result(self, query: str):
        # Simulate SQL result: [columns tuple, ...rows]
        if "fail" in query.lower():
            return [], False
        elif "empty" in query.lower():
            return [], True
        elif "numbers" in query.lower():
            return [{"id": 1, "val": 100}, {"id": 2, "val": 200}], True
        elif "singlecol" in query.lower():
            return [{"num": 42}, {"num": 13}], True
        elif "join" in query.lower():
            return [
                {"id": 1, "name": "Evan", "total": 10},
                {"id": 2, "name": "Kai", "total": 99},
            ], True
        else:
            return [{"a": 1, "b": 2}, {"a": 3, "b": 4}], True


@pytest.fixture
def result_fixtures():
    return ResultFixtures()


###########################
# 1. check_valid_SQL
###########################
@pytest.mark.asyncio
async def test_check_valid_sql_valid():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
        expected_sql_query="SELECT * FROM users",
    )
    out = await sql_syntax_validation(result)
    vprint("[check_valid_sql_valid]", out)
    assert out.score == 1


@pytest.mark.asyncio
async def test_check_valid_sql_invalid():
    result = ExampleResult(
        actual_sql_query="SHOULD NOT BE VALID SQL",
        expected_sql_query="SHOULD NOT BE VALID SQL",
    )
    out = await sql_syntax_validation(result)
    vprint("[check_valid_sql_invalid]", out)
    assert out.score == 0


@pytest.mark.asyncio
async def test_check_valid_sql_empty():
    result = ExampleResult(
        actual_sql_query="",
        expected_sql_query="",
    )
    out = await sql_syntax_validation(result)
    vprint("[check_valid_sql_empty]", out)
    assert out.score == 0


@pytest.mark.asyncio
async def test_check_valid_sql_case_insensitive():
    result = ExampleResult(
        actual_sql_query="select id from numbers",
        expected_sql_query="SELECT id FROM numbers",
    )
    out = await sql_syntax_validation(result)
    vprint("[check_valid_sql_case_insensitive]", out)
    assert out.score == 1


###########################
# 2. check_valid_sql_result
###########################
@pytest.mark.asyncio
async def test_check_valid_sql_result_success(result_fixtures):
    query = "SELECT * FROM numbers"
    actual_sql_result, is_valid_sql_result = result_fixtures.fake_result(query)
    result = ExampleResult(
        actual_sql_query=query,
        expected_sql_query=query,
        actual_sql_result=actual_sql_result,
        is_valid_sql_result=is_valid_sql_result,
    )

    out = await sql_execution_success(result)
    vprint("[check_valid_sql_result_success]", out)
    assert out.score == 1


@pytest.mark.asyncio
async def test_check_valid_sql_result_empty(result_fixtures):
    query = "SELECT * FROM empty"
    actual_sql_result, is_valid_sql_result = result_fixtures.fake_result(query)
    result = ExampleResult(
        actual_sql_query=query,
        expected_sql_query=query,
        actual_sql_result=actual_sql_result,
        is_valid_sql_result=is_valid_sql_result,
    )
    out = await sql_execution_success(result)
    vprint("[check_valid_sql_result_empty]", out)
    assert out.score == 1


@pytest.mark.asyncio
async def test_check_valid_sql_result_fail(result_fixtures):
    query = "SELECT * FROM fail"
    actual_sql_result, is_valid_sql_result = result_fixtures.fake_result(query)
    result = ExampleResult(
        actual_sql_query=query,
        expected_sql_query=query,
        actual_sql_result=actual_sql_result,
        is_valid_sql_result=is_valid_sql_result,
    )
    out = await sql_execution_success(result)
    vprint("[check_valid_sql_result_fail]", out)
    assert out.score == 0


@pytest.mark.asyncio
async def test_check_valid_sql_result_singlecol(result_fixtures):
    query = "SELECT * FROM singlecol"
    actual_sql_result, is_valid_sql_result = result_fixtures.fake_result(query)
    result = ExampleResult(
        actual_sql_query=query,
        expected_sql_query=query,
        actual_sql_result=actual_sql_result,
        is_valid_sql_result=is_valid_sql_result,
    )
    out = await sql_execution_success(result)
    vprint("[check_valid_sql_result_singlecol]", out)
    assert out.score == 1


@pytest.mark.asyncio
async def test_check_valid_sql_result_join(result_fixtures):
    query = "SELECT * FROM join"
    actual_sql_result, is_valid_sql_result = result_fixtures.fake_result(query)
    result = ExampleResult(
        actual_sql_query=query,
        expected_sql_query=query,
        actual_sql_result=actual_sql_result,
        is_valid_sql_result=is_valid_sql_result,
    )
    out = await sql_execution_success(result)
    vprint("[check_valid_sql_result_join]", out)
    assert out.score == 1


###########################
# 3. sql_query_type_similarity
###########################
@pytest.mark.asyncio
async def test_sql_query_type_similarity_exact():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM foo WHERE bar > 3",
    )
    out = await sql_command_types_match(result, {"query_type": ["filter"]})
    vprint("[sql_query_type_similarity_exact]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_sql_query_type_similarity_partial():
    result = ExampleResult(
        actual_sql_query="SELECT COUNT(*) FROM foo",
    )
    out = await sql_command_types_match(
        result, {"query_type": ["aggregation", "limit"]}
    )
    vprint("[sql_query_type_similarity_partial]", out)
    assert 0 < (out.score or 0.0) < 1.0


@pytest.mark.asyncio
async def test_sql_query_type_similarity_none():
    result = ExampleResult(
        actual_sql_query="",
    )
    out = await sql_command_types_match(result, {"query_type": []})
    vprint("[sql_query_type_similarity_none]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_sql_query_type_similarity_extra():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users ORDER BY id",
    )
    out = await sql_command_types_match(result, {"query_type": ["order_by"]})
    vprint("[sql_query_type_similarity_extra]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_sql_query_type_similarity_diff_sets():
    result = ExampleResult(
        actual_sql_query="SELECT name FROM users WHERE age > 30",
    )
    out = await sql_command_types_match(
        result, {"query_type": ["filter", "aggregation"]}
    )
    vprint("[sql_query_type_similarity_diff_sets]", out)
    assert 0 < (out.score or 0.0) < 1.0


###########################
# 4. sql_oso_models_used_similarity
###########################
@pytest.mark.asyncio
async def test_sql_oso_models_used_similarity_exact():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
    )
    out = await oso_tables_match(result, {"sql_models_used": ["users"]})
    vprint("[sql_oso_models_used_similarity_exact]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_sql_oso_models_used_similarity_partial():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users JOIN orders ON users.id=orders.uid",
    )
    out = await oso_tables_match(result, {"sql_models_used": ["users", "payments"]})
    vprint("[sql_oso_models_used_similarity_partial]", out)
    assert 0 < (out.score or 0.0) < 1.0


@pytest.mark.asyncio
async def test_sql_oso_models_used_similarity_none():
    result = ExampleResult(
        actual_sql_query="",
    )
    out = await oso_tables_match(result, {"sql_models_used": []})
    vprint("[sql_oso_models_used_similarity_none]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_sql_oso_models_used_similarity_multiple_tables():
    result = ExampleResult(
        actual_sql_query="SELECT u.id, o.id FROM users u, orders o",
    )
    out = await oso_tables_match(result, {"sql_models_used": ["users", "orders"]})
    vprint("[sql_oso_models_used_similarity_multiple_tables]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_sql_oso_models_used_similarity_mismatch():
    result = ExampleResult(
        actual_sql_query="SELECT u.id FROM users u",
    )
    out = await oso_tables_match(result, {"sql_models_used": ["orders"]})
    vprint("[sql_oso_models_used_similarity_mismatch]", out)
    assert 0 <= (out.score or 0.0) < 1.0


###########################
# 5. result_exact_match
###########################
@pytest.mark.asyncio
async def test_result_exact_match_success():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
        actual_sql_result=[{"a": 1, "b": 2}],
        expected_sql_result=[{"a": 1, "b": 2}],
        is_valid_sql_result=True,
        order_matters=True,
    )
    out = await results_exact_match(result)
    vprint("[result_exact_match_success]", out)
    assert out.score == 1


@pytest.mark.asyncio
async def test_result_exact_match_fail():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
        actual_sql_result=[{"a": 1, "b": 3}],
        expected_sql_result=[{"a": 1, "b": 2}],
        is_valid_sql_result=True,
        order_matters=True,
    )
    out = await results_exact_match(result)
    vprint("[result_exact_match_fail]", out)
    assert out.score == 0


@pytest.mark.asyncio
async def test_result_exact_match_not_valid():
    result = ExampleResult(
        actual_sql_query="",
    )
    out = await results_exact_match(result)
    vprint("[result_exact_match_not_valid]", out)
    assert out.score == 0.0


@pytest.mark.asyncio
async def test_result_exact_match_extra_row():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
        actual_sql_result=[{"col": 1}, {"col": 2}],
        expected_sql_result=[{"col": 1}],
        is_valid_sql_result=True,
        order_matters=True,
    )
    out = await results_exact_match(result)
    vprint("[result_exact_match_extra_row]", out)
    assert out.score == 0


@pytest.mark.asyncio
async def test_result_exact_match_extra_col():
    result = ExampleResult(
        actual_sql_query="SELECT a, b FROM table",
        actual_sql_result=[{"a": 1, "b": 2, "c": 3}],
        expected_sql_result=[{"a": 1, "b": 2}],
        is_valid_sql_result=True,
        order_matters=True,
    )
    out = await results_exact_match(result)
    vprint("[result_exact_match_extra_col]", out)
    assert out.score == 0


###########################
# 6. result_fuzzy_match
###########################
@pytest.mark.asyncio
async def test_result_fuzzy_match_perfect():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
        actual_sql_result=[{"a": 1}, {"a": 2}],
        expected_sql_result=[{"a": 1}, {"a": 2}],
        is_valid_sql_result=True,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_perfect]", out)
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_result_fuzzy_match_partial():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM users",
        actual_sql_result=[{"a": 1}, {"a": 3}],
        expected_sql_result=[{"a": 1}, {"a": 2}],
        is_valid_sql_result=True,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_partial]", out)
    assert 0 < (out.score or 0.0) < 1.0


@pytest.mark.asyncio
async def test_result_fuzzy_match_not_valid():
    result = ExampleResult(
        actual_sql_query="select 1",
        actual_sql_result=[],
        expected_sql_result=[],
        is_valid_sql_result=False,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_not_valid]", out)
    assert out.score == 0.0


@pytest.mark.asyncio
# note that we are using jaccards similarity here so while intuitively we might think that this should be 1/2, its actually 3/9
async def test_result_fuzzy_match_three_match_three_diff():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM fuzzy1",
        actual_sql_result=[
            {"a": 1},
            {"a": 2},
            {"a": 3},
            {"a": 99},
            {"a": 100},
            {"a": 101},
        ],
        expected_sql_result=[
            {"a": 1},
            {"a": 2},
            {"a": 3},
            {"a": 200},
            {"a": 201},
            {"a": 202},
        ],
        is_valid_sql_result=True,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_three_match_three_diff]", out)
    assert out.score == 1 / 3


@pytest.mark.asyncio
async def test_result_fuzzy_match_all_same_extra_col():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM fuzzy2",
        actual_sql_result=[{"a": 1, "b": 2}, {"a": 2, "b": 3}],
        expected_sql_result=[{"a": 1}, {"a": 2}],
        is_valid_sql_result=True,
        order_matters=False,
    )
    result.order_matters = False
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_all_same_extra_col]", out)
    assert out.score == 0


@pytest.mark.asyncio
async def test_result_fuzzy_match_eight_rows_one_off():
    base_rows = [{"col": i} for i in range(1, 9)]
    expected_rows = base_rows[:-1] + [{"col": 42}]
    result = ExampleResult(
        actual_sql_query="SELECT * FROM fuzzy3",
        actual_sql_result=base_rows,
        expected_sql_result=expected_rows,
        is_valid_sql_result=True,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_eight_rows_one_off]", out)
    assert 0 < (out.score or 0.0) < 1.0


@pytest.mark.asyncio
async def test_result_fuzzy_match_column_order_change():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM fuzzy4",
        actual_sql_result=[{"x": 1, "y": 2}, {"x": 3, "y": 4}],
        expected_sql_result=[{"y": 2, "x": 1}, {"y": 4, "x": 3}],
        is_valid_sql_result=True,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_column_order_change]", out)
    # Should be considered a match (score 1.0) if column permutation allowed
    assert out.score == 1.0


@pytest.mark.asyncio
async def test_result_fuzzy_match_all_empty():
    result = ExampleResult(
        actual_sql_query="SELECT * FROM fuzzy5",
        actual_sql_result=[],
        expected_sql_result=[],
        is_valid_sql_result=True,
        order_matters=False,
    )
    out = await results_similarity_score(result)
    vprint("[result_fuzzy_match_all_empty]", out)
    assert out.score == 1.0
