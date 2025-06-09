import json
import logging
import typing as t

import phoenix as px
from llama_index.core.base.response.schema import Response as ToolResponse
from oso_agent.agent.agent_registry import AgentRegistry
from oso_agent.tool.query_engine_tool import create_default_query_engine_tool
from phoenix.experiments import run_experiment
from phoenix.experiments.evaluators import ContainsAnyKeyword
from phoenix.experiments.types import Example
from pydantic import BaseModel, Field

from ..datasets.text2sql import TEXT2SQL_DATASET
from ..datasets.uploader import upload_dataset
from ..tool.oso_mcp_client import OsoMcpClient
from ..util.asyncbase import setup_nest_asyncio
from ..util.config import AgentConfig
from ..util.jaccard import jaccard_similarity_set, jaccard_similarity_str
from ..util.query import determine_query_type, determine_sql_models_used
from .valid_sql import is_valid_sql

setup_nest_asyncio()

EXPERIMENT_NAME = "text2sql-experiment"

logger = logging.getLogger(__name__)


class Text2SqlExperimentOptions(BaseModel):
    """Options for the text2sql experiment."""
    strategy: str = Field(
        default="default",
        description="The strategy to use for the text2sql experiment. "
                    "Currently only 'default' is supported.",
    )



async def text2sql_experiment(config: AgentConfig, _registry: AgentRegistry, _raw_options: dict[str, t.Any]):
    logger.info(f"Running text2sql experiment with: {config.model_dump_json()}")

    # Load the query engine tool
    query_engine_tool = await create_default_query_engine_tool(config)

    api_key = config.arize_phoenix_api_key.get_secret_value()

    logger.debug("Loading client")

    # We pass in the API key directly to the Phoenix client but it's likely 
    # ignored. See oso_agent/util/config.py
    phoenix_client = px.Client(
        endpoint=config.arize_phoenix_base_url,
        headers={
            "api_key": api_key,
        }
    )
    logger.debug("Uploading dataset")
    dataset = upload_dataset(phoenix_client, config.eval_dataset_text2sql, TEXT2SQL_DATASET)

    async def task(example: Example) -> str:
        # print(f"Example: {example}")
        question = str(example.input["question"])
        # print(f"Question: {question}")
        # expected = str(example.output["answer"])
        # print(f"Expected: {expected}")
        tool_output = await query_engine_tool.acall(input=question)
        logger.debug(f"Query engine response: {tool_output}")

        raw_output = tool_output.raw_output
        if not isinstance(raw_output, ToolResponse):
            return f"Unexpected tool output type: {type(raw_output)}"
        

        if raw_output.metadata is None:
            return "No metadata in query engine tool output"
        
        return raw_output.metadata.get("sql_query", "No SQL query in metadata")

    contains_select = ContainsAnyKeyword(keywords=["SELECT"])

    def load_expected_sql_answer(expected: dict[str, t.Any]) -> str:
        """Load the expected answer from the example."""
        expected_answer = expected.get("answer")
        if not expected_answer:
            logger.warning("No expected answer provided, defaulting to 'SELECT 1'")
            expected_answer = "SELECT 1"
        return expected_answer

    def sql_query_type_similarity(output: str, expected: dict[str, t.Any]) -> float:
        """Evaluate the similarity between the output and expected SQL query types using Jaccard similarity."""
        output_query_types = determine_query_type(output)
        expected_query_types = expected.get('query_type') or []

        return jaccard_similarity_set(set(output_query_types), set(expected_query_types))

    def sql_oso_models_used_similarity(output: str, expected: dict[str, t.Any]) -> float:
        """Evaluate the similarity between the output and expected oso models used using Jaccard similarity."""
        output_oso_models_used = determine_sql_models_used(output)
        expected_oso_models_used = expected.get('sql_models_used') or []

        return jaccard_similarity_set(set(output_oso_models_used), set(expected_oso_models_used))

    logger.debug("Creating Oso MCP client")
    oso_mcp_client = OsoMcpClient(config.oso_mcp_url)
    async def sql_result_similarity(output: str, expected: dict[str, t.Any]) -> float:
        """Evaluate the similarity between results post-query"""
        expected_answer = load_expected_sql_answer(expected)
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

    evaluators = [
        contains_select,
        sql_query_type_similarity,
        sql_oso_models_used_similarity,
        sql_result_similarity,
    ]

    logger.debug("Running experiment")
    experiment = run_experiment(
        dataset,
        task,
        experiment_name=EXPERIMENT_NAME,
        evaluators=evaluators,
        experiment_metadata={ "agent_name": config.agent_name }
    )
    return experiment
