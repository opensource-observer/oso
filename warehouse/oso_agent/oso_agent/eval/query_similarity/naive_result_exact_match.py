import json
import typing as t

from ...tool.oso_mcp_client import OsoMcpClient
from ...util.jaccard import jaccard_similarity_str
from ...util.query import load_expected_sql_answer, sanitize_query_from_agent
from ..valid_sql import is_valid_sql


def make_naive_exec_match_evaluator(oso_mcp_client: OsoMcpClient) -> t.Callable[[str, t.Dict[str, t.Any]], t.Awaitable[float]]:

    async def _naive_result_sim(output: str, expected: dict[str, t.Any]) -> float:
        """Evaluate the similarity between results post-query"""
        expected_answer = load_expected_sql_answer(expected)
        expected_answer = sanitize_query_from_agent(expected_answer)
        expected_response = await oso_mcp_client.query_oso(expected_answer)
        expected_str = json.dumps(expected_response)
        # print(f"Expected Str: {expected_str}")

        # We might be testing agents that produce SQL or text results
        if is_valid_sql(output, dialect="trino"):
            # If the output is a valid SQL query, we can run it against the OSO MCP client and compare results
            output_response = await oso_mcp_client.query_oso(output)
            output_str = json.dumps(output_response)
            return jaccard_similarity_str(output_str, expected_str)
            # print(f"Output Response: {output_str}")
        else:
            # Otherwise, just try to compare the output directly
            return jaccard_similarity_str(output, expected_str)
        
    return _naive_result_sim