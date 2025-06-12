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
from ..types.eval import Text2SQLExperimentWorkflow
from ..util.asyncbase import setup_nest_asyncio
from ..util.config import AgentConfig

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

    # check if specific evals have been defined
    example_ids = _raw_options.get('example_ids')
    dataset_name = "local_run_text2sql_experiment" if example_ids else config.eval_dataset_text2sql 
    dataset = upload_dataset(phoenix_client, TEXT2SQL_DATASET, dataset_name, config, example_ids)

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

    logger.debug("Creating Oso MCP client")
    oso_mcp_client = OsoMcpClient(config.oso_mcp_url)

    workflow = Text2SQLExperimentWorkflow(oso_mcp_client=oso_mcp_client, keep_distinct=True)

    evaluators = [
        contains_select,
        workflow.check_valid_SQL,
        workflow.check_valid_SQL_result,
        workflow.sql_query_type_similarity,
        workflow.sql_oso_models_used_similarity,
        workflow.result_exact_match,
        workflow.result_fuzzy_match
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
