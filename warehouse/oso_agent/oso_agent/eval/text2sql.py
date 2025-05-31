import json
import logging
from typing import Any, Dict

import nest_asyncio
import phoenix as px
from metrics_tools.semantic.testing import setup_registry
from phoenix.experiments import run_experiment
from phoenix.experiments.evaluators import ContainsAnyKeyword
from phoenix.experiments.types import Example

from ..datasets.text2sql import TEXT2SQL_DATASET
from ..datasets.uploader import upload_dataset
from ..tool.oso_mcp_client import OsoMcpClient
from ..types import (
    ErrorResponse,
    SemanticResponse,
    SqlResponse,
    StrResponse,
    WrappedResponseAgent,
)
from ..util.config import AgentConfig
from ..util.jaccard import jaccard_similarity_str
from .valid_sql import is_valid_sql

EXPERIMENT_NAME = "text2sql-experiment"
try:
    nest_asyncio.apply()
except ValueError:
    pass

logger = logging.getLogger(__name__)


async def text2sql_experiment(config: AgentConfig, agent: WrappedResponseAgent):
    logger.info(f"Running text2sql experiment with: {config.model_dump_json()}")
    api_key = config.arize_phoenix_api_key.get_secret_value()

    # We pass in the API key directly to the Phoenix client but it's likely 
    # ignored. See oso_agent/util/config.py
    phoenix_client = px.Client(
        endpoint=config.arize_phoenix_base_url,
        headers={
            "api_key": api_key,
        }
    )
    dataset = upload_dataset(phoenix_client, config.eval_dataset_text2sql, TEXT2SQL_DATASET)

    async def task(example: Example) -> str:
        # print(f"Example: {example}")
        question = str(example.input["question"])
        # print(f"Question: {question}")
        # expected = str(example.output["answer"])
        # print(f"Expected: {expected}")
        agent_response = await agent.run_safe(question)
        logger.debug(f"Agent response: {agent_response}")

        match agent_response.response:
            case StrResponse(blob=blob):
                return blob
            case SemanticResponse(query=query):
                # hacky way for now to load the semantic registry
                semantic_registry = setup_registry()
                try:
                    return semantic_registry.query(query).sql(dialect="trino", pretty=True)
                except Exception as e:
                    return f"Error rendering semantic query: {e}"
            case SqlResponse(query=query):
                return query.query
            case ErrorResponse(message=message):
                return message

    contains_select = ContainsAnyKeyword(keywords=["SELECT"])

    def load_expected_sql_answer(expected: Dict[str, Any]) -> str:
        """Load the expected answer from the example."""
        expected_answer = expected.get("answer")
        if not expected_answer:
            logger.warning("No expected answer provided, defaulting to 'SELECT 1'")
            expected_answer = "SELECT 1"
        return expected_answer

    def sql_query_similarity(output: str, expected: Dict[str, Any]) -> float:
        """Evaluate the similarity between the output and expected SQL query using Jaccard similarity."""
        expected_answer = load_expected_sql_answer(expected)
        # print(f"Output: {output}, expected: {expected_answer}")
        return jaccard_similarity_str(output, expected_answer)

    oso_mcp_client = OsoMcpClient(config.oso_mcp_url)
    def sql_result_similarity(output: str, expected: Dict[str, Any]) -> float:
        """Evaluate the similarity between results post-query"""
        expected_answer = load_expected_sql_answer(expected)
        expected_response = oso_mcp_client.query_oso(expected_answer)
        expected_str = json.dumps(expected_response)
        # print(f"Expected Str: {expected_str}")

        # We might be testing agents that produce SQL or text results
        if is_valid_sql(output, dialect="trino"):
            # If the output is a valid SQL query, we can run it against the OSO MCP client and compare results
            output_response = oso_mcp_client.query_oso(output)
            output_str = json.dumps(output_response)
            return jaccard_similarity_str(output_str, expected_str)
            # print(f"Output Response: {output_str}")
        else:
            # Otherwise, just try to compare the output directly
            return jaccard_similarity_str(output, expected_str)

    evaluators = [
        contains_select,
        sql_query_similarity,
        sql_result_similarity,
    ]

    experiment = run_experiment(
        dataset,
        task,
        experiment_name=EXPERIMENT_NAME,
        evaluators=evaluators,
        experiment_metadata={ "agent_name": config.agent_name }
    )
    return experiment
