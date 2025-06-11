import logging
import typing as t

from oso_agent.util.errors import AgentRuntimeError

from ...tool.oso_mcp_client import OsoMcpClient
from ...util.parse import postprocess, remove_distinct, replace_cur_year, result_eq
from ...util.query import load_expected_sql_answer, sanitize_query_from_agent

logger = logging.getLogger(__name__)

async def exec_on_db(oso_mcp_client, query: str):
    query = replace_cur_year(query)
    try:
        rows = await oso_mcp_client.query_oso(query)
    except AgentRuntimeError as e:
        # Known failure (invalid SQL, missing table, etc.)
        logger.warning(f"Oso MCP client query failed: {e}")
        return None
    except Exception as e:
        # Unknown failure
        logger.exception(f"Unexpected error when running query: {query}\n{e}")
        return None

    if not rows:
        return []

    columns = list(rows[0].keys())
    tuples = [tuple(row[col] for col in columns) for row in rows]
    return tuples



def make_result_exact_match_evaluator(oso_mcp_client: OsoMcpClient, keep_distinct: bool = True) -> t.Callable[[str, dict[str, t.Any]], t.Awaitable[int]]:
    async def result_exec_match(output: str, expected: dict[str, t.Any]) -> int:
        answer = load_expected_sql_answer(expected)
        output, answer = sanitize_query_from_agent(output), sanitize_query_from_agent(answer)
        output, answer = postprocess(output), postprocess(answer)
        if not keep_distinct:
            output = remove_distinct(output)
            answer = remove_distinct(answer)

        if not output or not answer:
            logger.warning(f"Empty output or expected: output='{output}', answer='{answer}'")
            return -1

        order_matters = 'order by' in answer.lower()

        agent_response = await exec_on_db(oso_mcp_client, output)
        gold_response = await exec_on_db(oso_mcp_client, answer)

        # Handle SQL execution or parsing errors
        if agent_response is None or gold_response is None:
            logger.warning(
                f"SQL execution failed for: output='{output}', answer='{answer}', "
                f"agent_response={agent_response}, gold_response={gold_response}"
            )
            return -1

        try:
            return int(result_eq(agent_response, gold_response, order_matters=order_matters))
        except Exception as e:
            logger.exception(f"Result comparison failed: {e}")
            return -1
    return result_exec_match
