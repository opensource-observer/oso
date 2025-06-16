import pandas as pd
import pytest

from ..types.eval import ExampleResult, OsoMcpClient, Text2SQLExperimentWorkflow

VERBOSE = True
def vprint(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)

# Dummy stub for local testing
class DummyWorkflow(Text2SQLExperimentWorkflow):
    def __init__(self):
        self.oso_mcp_client = OsoMcpClient("")
        self.keep_distinct = True
        self.cache = {}

    async def exec_on_db(self, query: str):
        # Simulate SQL result: [columns tuple, ...rows]
        if "fail" in query.lower():
            return [], False
        elif "empty" in query.lower():
            return [("id", "name")], True
        elif "numbers" in query.lower():
            return [("id", "val"), (1, 100), (2, 200)], True
        elif "singlecol" in query.lower():
            return [("num",), (42,), (13,)], True
        elif "join" in query.lower():
            return [("id", "name", "total"), (1, "Evan", 10), (2, "Kai", 99)], True
        else:
            return [("a", "b"), (1, 2), (3, 4)], True

    def df_info_str(self, rows):
        if not rows or len(rows) <= 1:
            return "Empty table (0 rows)"
        columns = rows[0]
        data = rows[1:]
        df = pd.DataFrame(data, columns=columns)
        return f"{df.shape[0]} rows x {df.shape[1]} cols"

    def _get_example_result_from_id(self, id: str):
        if id not in self.cache:
            self.cache[id] = ExampleResult()
        return self.cache[id]


@pytest.fixture
def workflow():
    return DummyWorkflow()

###########################
# 1. check_valid_SQL
###########################
def test_check_valid_SQL_valid(workflow):
    out = workflow.check_valid_SQL("SELECT * FROM users", {"answer": "SELECT * FROM users"}, {"id": "test1"})
    vprint("[check_valid_SQL_valid]", out)
    assert out.score == 1

def test_check_valid_SQL_invalid(workflow):
    out = workflow.check_valid_SQL("SELCT FROM", {"answer": "SELECT * FROM users"}, {"id": "test2"})
    vprint("[check_valid_SQL_invalid]", out)
    assert out.score == 0

def test_check_valid_SQL_empty(workflow):
    out = workflow.check_valid_SQL("", {"answer": ""}, {"id": "test3"})
    vprint("[check_valid_SQL_empty]", out)
    assert out.score == 0

def test_check_valid_SQL_case_insensitive(workflow):
    out = workflow.check_valid_SQL("select id from numbers", {"answer": "SELECT id FROM numbers"}, {"id": "test19"})
    vprint("[check_valid_SQL_case_insensitive]", out)
    assert out.score == 1

def test_check_valid_SQL_bogus(workflow):
    out = workflow.check_valid_SQL("This is not SQL", {"answer": "SELECT * FROM numbers"}, {"id": "test20"})
    vprint("[check_valid_SQL_bogus]", out)
    assert out.score == 0

###########################
# 2. check_valid_SQL_result
###########################
@pytest.mark.asyncio
async def test_check_valid_SQL_result_success(workflow):
    eid = "test4"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM numbers"
    out = await workflow.check_valid_SQL_result({"id": eid})
    vprint("[check_valid_SQL_result_success]", out)
    assert out.score == 1

@pytest.mark.asyncio
async def test_check_valid_SQL_result_empty(workflow):
    eid = "test5"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM empty"
    out = await workflow.check_valid_SQL_result({"id": eid})
    vprint("[check_valid_SQL_result_empty]", out)
    assert out.score == 1

@pytest.mark.asyncio
async def test_check_valid_SQL_result_fail(workflow):
    eid = "test6"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM fail"
    out = await workflow.check_valid_SQL_result({"id": eid})
    vprint("[check_valid_SQL_result_fail]", out)
    assert out.score == 0

@pytest.mark.asyncio
async def test_check_valid_SQL_result_singlecol(workflow):
    eid = "test6b"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM singlecol"
    out = await workflow.check_valid_SQL_result({"id": eid})
    vprint("[check_valid_SQL_result_singlecol]", out)
    assert out.score == 1

@pytest.mark.asyncio
async def test_check_valid_SQL_result_join(workflow):
    eid = "test6c"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM join"
    out = await workflow.check_valid_SQL_result({"id": eid})
    vprint("[check_valid_SQL_result_join]", out)
    assert out.score == 1

###########################
# 3. sql_query_type_similarity
###########################
def test_sql_query_type_similarity_exact(workflow):
    eid = "test7"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM foo WHERE bar > 3"
    out = workflow.sql_query_type_similarity({"id": eid, "query_type": ["filter"]})
    vprint("[sql_query_type_similarity_exact]", out)
    assert out.score == 1.0

def test_sql_query_type_similarity_partial(workflow):
    eid = "test8"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT COUNT(*) FROM foo"
    out = workflow.sql_query_type_similarity({"id": eid, "query_type": ["aggregation", "limit"]})
    vprint("[sql_query_type_similarity_partial]", out)
    assert 0 < out.score < 1.0

def test_sql_query_type_similarity_none(workflow):
    eid = "test9"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = ""
    out = workflow.sql_query_type_similarity({"id": eid, "query_type": []})
    vprint("[sql_query_type_similarity_none]", out)
    assert out.score == 1.0

def test_sql_query_type_similarity_extra(workflow):
    eid = "test9b"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM users ORDER BY id"
    out = workflow.sql_query_type_similarity({"id": eid, "query_type": ["order_by"]})
    vprint("[sql_query_type_similarity_extra]", out)
    assert out.score == 1.0

def test_sql_query_type_similarity_diff_sets(workflow):
    eid = "test9c"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT name FROM users WHERE age > 30"
    out = workflow.sql_query_type_similarity({"id": eid, "query_type": ["filter", "aggregation"]})
    vprint("[sql_query_type_similarity_diff_sets]", out)
    assert 0 < out.score < 1.0

###########################
# 4. sql_oso_models_used_similarity
###########################
def test_sql_oso_models_used_similarity_exact(workflow):
    eid = "test10"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM users"
    out = workflow.sql_oso_models_used_similarity({"id": eid, "sql_models_used": ["users"]})
    vprint("[sql_oso_models_used_similarity_exact]", out)
    assert out.score == 1.0

def test_sql_oso_models_used_similarity_partial(workflow):
    eid = "test11"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT * FROM users JOIN orders ON users.id=orders.uid"
    out = workflow.sql_oso_models_used_similarity({"id": eid, "sql_models_used": ["users", "payments"]})
    vprint("[sql_oso_models_used_similarity_partial]", out)
    assert 0 < out.score < 1.0

def test_sql_oso_models_used_similarity_none(workflow):
    eid = "test12"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = ""
    out = workflow.sql_oso_models_used_similarity({"id": eid, "sql_models_used": []})
    vprint("[sql_oso_models_used_similarity_none]", out)
    assert out.score == 1.0

def test_sql_oso_models_used_similarity_multiple_tables(workflow):
    eid = "test12b"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT u.id, o.id FROM users u, orders o"
    out = workflow.sql_oso_models_used_similarity({"id": eid, "sql_models_used": ["users", "orders"]})
    vprint("[sql_oso_models_used_similarity_multiple_tables]", out)
    assert out.score == 1.0

def test_sql_oso_models_used_similarity_mismatch(workflow):
    eid = "test12c"
    result = workflow._get_example_result_from_id(eid)
    result.cleaned_agent_query = "SELECT u.id FROM users u"
    out = workflow.sql_oso_models_used_similarity({"id": eid, "sql_models_used": ["orders"]})
    vprint("[sql_oso_models_used_similarity_mismatch]", out)
    assert 0 <= out.score < 1.0

###########################
# 5. result_exact_match
###########################
@pytest.mark.asyncio
async def test_result_exact_match_success(workflow):
    eid = "test13"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a", "b"), (1, 2)]
    result.expected_sql_result = [("a", "b"), (1, 2)]
    result.order_matters = True
    out = await workflow.result_exact_match({"id": eid})
    vprint("[result_exact_match_success]", out)
    assert out.score == 1

@pytest.mark.asyncio
async def test_result_exact_match_fail(workflow):
    eid = "test14"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a", "b"), (1, 3)]
    result.expected_sql_result = [("a", "b"), (1, 2)]
    result.order_matters = True
    out = await workflow.result_exact_match({"id": eid})
    vprint("[result_exact_match_fail]", out)
    assert out.score == 0

@pytest.mark.asyncio
async def test_result_exact_match_not_valid(workflow):
    eid = "test15"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = False
    out = await workflow.result_exact_match({"id": eid})
    vprint("[result_exact_match_not_valid]", out)
    assert out.score == -1

@pytest.mark.asyncio
async def test_result_exact_match_extra_row(workflow):
    eid = "test15b"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("col",), (1,), (2,)]
    result.expected_sql_result = [("col",), (1,)]
    result.order_matters = True
    out = await workflow.result_exact_match({"id": eid})
    vprint("[result_exact_match_extra_row]", out)
    assert out.score == 0

@pytest.mark.asyncio
async def test_result_exact_match_extra_col(workflow):
    eid = "test15c"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a", "b", "c"), (1, 2, 3)]
    result.expected_sql_result = [("a", "b"), (1, 2)]
    result.order_matters = True
    out = await workflow.result_exact_match({"id": eid})
    vprint("[result_exact_match_extra_col]", out)
    assert out.score == 0

###########################
# 6. result_fuzzy_match
###########################
@pytest.mark.asyncio
async def test_result_fuzzy_match_perfect(workflow):
    eid = "test16"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a",), (1,), (2,)]
    result.expected_sql_result = [("a",), (1,), (2,)]
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_perfect]", out)
    assert out.score == 1.0

@pytest.mark.asyncio
async def test_result_fuzzy_match_partial(workflow):
    eid = "test17"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a",), (1,), (3,)]
    result.expected_sql_result = [("a",), (1,), (2,)]
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_partial]", out)
    assert 0 < out.score < 1.0

@pytest.mark.asyncio
async def test_result_fuzzy_match_not_valid(workflow):
    eid = "test18"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_not_valid]", out)
    assert out.score == -1

@pytest.mark.asyncio
# note that we are using jaccards similarity here so while intuitively we might think that this should be 1/2, its actually 3/9
async def test_result_fuzzy_match_three_match_three_diff(workflow):
    eid = "fuzzy1"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a",), (1,), (2,), (3,), (99,), (100,), (101,)]
    result.expected_sql_result = [("a",), (1,), (2,), (3,), (200,), (201,), (202,)]
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_three_match_three_diff]", out)
    assert out.score == 1/3

@pytest.mark.asyncio
async def test_result_fuzzy_match_all_same_extra_col(workflow):
    eid = "fuzzy2"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("a", "b"), (1, 2), (2, 3)]
    result.expected_sql_result = [("a",), (1,), (2,)]
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_all_same_extra_col]", out)
    assert out.score == 0

@pytest.mark.asyncio
async def test_result_fuzzy_match_eight_rows_one_off(workflow):
    eid = "fuzzy3"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    base_rows = [(i,) for i in range(1, 9)]
    agent_rows = [("col",)] + base_rows
    expected_rows = [("col",)] + base_rows[:-1] + [(42,)]
    result.agent_sql_result = agent_rows
    result.expected_sql_result = expected_rows
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_eight_rows_one_off]", out)
    assert 0 < out.score < 1.0

@pytest.mark.asyncio
async def test_result_fuzzy_match_column_order_change(workflow):
    eid = "fuzzy4"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("x", "y"), (1, 2), (3, 4)]
    result.expected_sql_result = [("y", "x"), (2, 1), (4, 3)]
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_column_order_change]", out)
    # Should be considered a match (score 1.0) if column permutation allowed
    assert out.score == 1.0

@pytest.mark.asyncio
async def test_result_fuzzy_match_all_empty(workflow):
    eid = "fuzzy5"
    result = workflow._get_example_result_from_id(eid)
    result.is_valid_sql_result = True
    result.agent_sql_result = [("col",)]
    result.expected_sql_result = [("col",)]
    result.order_matters = False
    out = await workflow.result_fuzzy_match({"id": eid})
    vprint("[result_fuzzy_match_all_empty]", out)
    assert out.score == 1.0
