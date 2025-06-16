import logging
import typing as t
from io import StringIO

import pandas as pd
from oso_agent.util.errors import AgentRuntimeError
from phoenix.experiments.types import EvaluationResult
from pydantic import BaseModel, Field

from ..eval.valid_sql import is_valid_sql
from ..tool.oso_mcp_client import OsoMcpClient
from ..util.jaccard import jaccard_similarity_set
from ..util.parse import postprocess, remove_distinct, replace_cur_year
from ..util.query import (
    determine_query_type,
    determine_sql_models_used,
    load_expected_sql_answer,
    sanitize_query_from_agent,
)
from ..util.query_sim import result_eq_bool, result_eq_float_w_metadata

logger = logging.getLogger(__name__)

# struct
class ExampleResult(BaseModel):
    raw_agent_response: str = ""
    cleaned_agent_query: str = ""
    is_valid_sql_query: bool = False
    order_matters: bool = False
    expected_query: str = ""
    agent_sql_result: list[tuple] = Field(default_factory=list)
    is_valid_sql_result: bool = False
    expected_sql_result: list[tuple] = Field(default_factory=list)


class Text2SQLExperimentWorkflow():
    oso_mcp_client: OsoMcpClient
    keep_distinct: bool
    cache: dict

    # clean data
    # execute
    # handle errors
    # run evals

    # eval 1: check valid SQL (this will populate ExampleResult, clean and prepare SQL, and return if valid SQL has passed)
    # eval 2: if the above works then we will run check valid result (as metadata maybe print a .info())
    # eval 3: query type comparison (metadata should be each set printed)
    # eval 4: oso models used (metadata should be each set printed)
    # eval 5: result exact match (.info() of each df?)
    # eval 6: result fuzzy match (.info() of each df?, maybe some info on why it's fuzzy)

    # ensure all evals now follow this layout:
    # return {
    #     "score": 1.0,
    #     "label": "exact match",
    #     "metadata": {"foo": "bar", "trace_id": "12345"}
    # }


    def __init__(self, oso_mcp_client: OsoMcpClient, keep_distinct: bool) -> None:
        self.oso_mcp_client = oso_mcp_client
        self.keep_distinct = keep_distinct
        self.cache = {}    # id -> ExampleResult


    # query the db and prepare the result
    async def exec_on_db(self, query: str) -> t.Tuple[t.List[t.Tuple[t.Any, ...]], bool]:
        valid_result, rows, tuples = True, None, []

        logger.info("querying with:", query)
        
        try:
            rows = await self.oso_mcp_client.query_oso(query)
            logger.info("rows:", rows)
        except AgentRuntimeError as e:
            logger.warning(f"Oso MCP client query failed: {e}")
            valid_result = False
        except Exception as e:
            logger.exception(f"Unexpected error when running query: {query}\n{e}")
            valid_result = False

        if valid_result and rows:
            columns = list(rows[0].keys())
            # treat the top row as column names
            tuples = [tuple(columns)] + [tuple(row[col] for col in columns) for row in rows]
            logger.info("columns:", columns)
            logger.info("tuples:", tuples)
        return tuples, valid_result


    def df_info_str(self, rows: t.List[t.Tuple]):
        if not rows or len(rows) <= 1 or not isinstance(rows[0], tuple):
            return "Empty table (0 rows)"
        try:
            columns = rows[0]
            data = rows[1:]
            df = pd.DataFrame(data, columns=columns)
            buf = StringIO()
            df.info(buf=buf)
            return buf.getvalue()
        except Exception as e:
            return f"Error generating DataFrame info: {e}"


    def _get_example_result_from_id(self, id: str) -> ExampleResult:
        if id not in self.cache:
            self.cache[id] = ExampleResult()
        return self.cache[id]
    

    # eval 1: check valid SQL (this will populate ExampleResult, clean and prepare SQL, and return if valid SQL has passed)
    def check_valid_SQL(self, output: str, expected: dict[str, t.Any], metadata: dict[str, t.Any]) -> EvaluationResult:
        example_result = self._get_example_result_from_id(metadata["id"])
        example_result.raw_agent_response = output
        expected_answer = load_expected_sql_answer(expected)

        # sanitize and check if the agent's response is valid SQL
        output_clean, expected_answer_clean = sanitize_query_from_agent(output), sanitize_query_from_agent(expected_answer)
        example_result.is_valid_sql_query = is_valid_sql(output_clean)

        # continue cleaning the query
        output_clean, expected_answer_clean = postprocess(output_clean), postprocess(expected_answer_clean)
        output_clean, expected_answer_clean = replace_cur_year(output_clean), replace_cur_year(output_clean)
        if not self.keep_distinct:
            output_clean = remove_distinct(output_clean)
            expected_answer_clean = remove_distinct(expected_answer_clean)
        
        # store in ExampleResult obj
        example_result.cleaned_agent_query = output_clean
        example_result.expected_query = expected_answer_clean
        example_result.order_matters = 'order by' in expected_answer_clean.lower()

        return EvaluationResult(
            score=int(example_result.is_valid_sql_query),
            label="is_agent_response_valid_sql",
            explanation="Returns a boolean for if the agent's output query is valid (can be parsed by sqlglot)",
            metadata={
                "cleaned_agent_query": example_result.cleaned_agent_query,
            }
        )
    

    # eval 2: if the above works then we will run check valid result (as metadata maybe print a .info())
    async def check_valid_SQL_result(self, metadata: dict[str, t.Any]) -> EvaluationResult:
        example_result = self._get_example_result_from_id(metadata["id"])
        agent_sql_result, example_result.is_valid_sql_result = await self.exec_on_db(example_result.cleaned_agent_query)

        info_str = ""
        if example_result.is_valid_sql_result:
            # since we know that the agent returned a valid query we will populate the expected sql result for later comparisons
            example_result.expected_sql_result, _ = await self.exec_on_db(example_result.expected_query)           
            example_result.agent_sql_result = agent_sql_result
            # add metadata
            info_str = self.df_info_str(agent_sql_result)
        else:
            # empty tables should at least have 1 row (column names) so if we get here then something failed
            info_str = "Query execution failed or table does not exist."
        return EvaluationResult(
            score=int(example_result.is_valid_sql_result),
            label="does_agent_query_return_valid_result",
            explanation="Returns a boolean for if the agent's query returns a valid SQL table (empty table is considered equal)",
            metadata={
                "agent_sql_result_info": info_str
            }
        )


    # eval 3: query type comparison (metadata should be each set printed)
    def sql_query_type_similarity(self, metadata: dict[str, t.Any]) -> EvaluationResult:
        example_result = self._get_example_result_from_id(metadata["id"])
        
        output_query_types = set(determine_query_type(example_result.cleaned_agent_query))
        expected_query_types = set(metadata.get('query_type') or [])

        return EvaluationResult(
            score=jaccard_similarity_set(output_query_types, expected_query_types),
            label="query_type_similarity",
            explanation="Jaccard's similarity over the types of functions present in each SQL query",
            metadata={
                "output_query_types": sorted(output_query_types),
                "expected_query_types": sorted(expected_query_types),
            }
        )


    # eval 4: oso models used (metadata should be each set printed)
    def sql_oso_models_used_similarity(self, metadata: dict[str, t.Any]) -> EvaluationResult:
        example_result = self._get_example_result_from_id(metadata["id"])

        output_oso_models_used = set(determine_sql_models_used(example_result.cleaned_agent_query))
        expected_oso_models_used = set(metadata.get('sql_models_used') or [])

        return EvaluationResult(
            score=jaccard_similarity_set(output_oso_models_used, expected_oso_models_used),
            label="sql_models_used_similarity",
            explanation="Jaccard's similarity over the tables each query uses",
            metadata={
                "output_oso_models_used": sorted(output_oso_models_used),
                "expected_oso_models_used": sorted(expected_oso_models_used),
            }
        )


    # eval 5: result exact match (.info() of each df?)
    async def result_exact_match(self, metadata: dict[str, t.Any]) -> EvaluationResult:
        example_result = self._get_example_result_from_id(metadata["id"])
        
        if example_result.is_valid_sql_result:
            try:
                score = int(result_eq_bool(example_result.agent_sql_result[1:], example_result.expected_sql_result[1:], order_matters=example_result.order_matters))
            except Exception as e:
                logger.exception(f"Result comparison failed: {e}")
                score = -1
        else:
            score = -1

        return EvaluationResult(
            score=score,
            label="sql_result_exact_match",
            explanation="A boolean that reflects if the pandas result of the agent's query EXACTLY matches the expected result",
            metadata={
                "agent_result_info": self.df_info_str(example_result.agent_sql_result),
                "expected_result_info": self.df_info_str(example_result.expected_sql_result)
            }
        )


    # eval 6: result fuzzy match (.info() of each df?, maybe some info on why it's fuzzy)
    async def result_fuzzy_match(self, metadata: dict[str, t.Any]) -> EvaluationResult:
        example_result = self._get_example_result_from_id(metadata["id"])
        fuzzy_metadata = {}

        if example_result.is_valid_sql_result:
            try:
                score, fuzzy_metadata = result_eq_float_w_metadata(example_result.agent_sql_result[1:], example_result.expected_sql_result[1:], order_matters=example_result.order_matters)
                score = float(score) # just to be safe
            except Exception as e:
                logger.exception(f"Result comparison failed: {e}")
                score = -1
                fuzzy_metadata = {}
        else:
            score = -1

        return EvaluationResult(
            score=score,
            label="sql_result_fuzzy_match",
            explanation="A float value that reflects how similar the result of the agent's query is to the expected result | 0 = no similarities, 1 = exact match",
            metadata={
                "agent_result_info": self.df_info_str(example_result.agent_sql_result),
                "expected_result_info": self.df_info_str(example_result.expected_sql_result),
                "fuzzy_match_info": fuzzy_metadata
            }
        )
    
