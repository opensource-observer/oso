import logging
import typing as t

import phoenix as px
from llama_index.core.workflow import StartEvent, StopEvent, step
from oso_agent.agent.agent_registry import AgentRegistry
from oso_agent.eval.experiment_runner import ExperimentRunner
from oso_agent.tool.llm import create_llm
from oso_agent.tool.query_engine_tool import create_default_query_engine_tool
from oso_agent.types.eval import ExampleResult
from oso_agent.types.response import StrResponse
from oso_agent.util.query import clean_query_for_eval
from oso_agent.workflows import ResourceResolver
from oso_agent.workflows.base import MixableWorkflow
from oso_agent.workflows.eval import EvalWorkflowResult
from oso_agent.workflows.text2sql.basic import BasicText2SQL
from oso_agent.workflows.types import SQLResultEvent, Text2SQLGenerationEvent
from phoenix.experiments.types import EvaluationResult, Example
from pydantic import BaseModel, Field

from ...datasets.text2sql import TEXT2SQL_DATASET
from ...datasets.uploader import upload_dataset
from ...tool.oso_mcp_client import OsoMcpClient
from ...util.asyncbase import setup_nest_asyncio
from ...util.config import AgentConfig
from .evals import (
    check_valid_sql,
    check_valid_sql_result,
    result_exact_match,
    result_fuzzy_match,
    sql_oso_models_used_similarity,
    sql_query_type_similarity,
)

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


class FakeWorkflow(MixableWorkflow):
    @step
    async def handle_start(self, start_event: StartEvent) -> StopEvent:
        """Handle the start event of the workflow."""
        print("hereerererereer")
        # This is a fake workflow for testing purposes
        return StopEvent(result=StrResponse(blob="Fake response"))
    
async def post_process_result(
    example: Example, result: EvalWorkflowResult, resolver: ResourceResolver
):
    """Post-process the result of the experiment."""
    expected = str(example.output["answer"])

    oso_mcp_client = t.cast(OsoMcpClient, resolver.get_resource("oso_mcp_client"))
    try:
        expected_sql_result = await oso_mcp_client.query_oso(expected)
    except Exception as e:
        logger.error(f"Error querying oso mcp client for expected result: {e}")
        expected_sql_result = []

    if not isinstance(expected_sql_result, list):
        expected_sql_result = t.cast(list[dict[str, t.Any]], [])

    final_result = result.final_result
    raw_agent_response = None
    if final_result:
        raw_agent_response = final_result.response

    actual_generated_sql = ""
    actual_sql_result: list[dict[str, t.Any]] = []
    # Find actual result

    is_valid_sql_result = False
    # Hacky but for now we only expect one Text2SQLGenerationEvent and one
    # SQLResultEvent. This should be refactored in the future to handle
    # multiple events
    for event in result.events:
        if isinstance(event, Text2SQLGenerationEvent):
            actual_generated_sql = event.output_sql
        if isinstance(event, SQLResultEvent):
            if not event.error:
                is_valid_sql_result = True
            if isinstance(event.results, list):
                actual_sql_result = t.cast(list[dict[str, t.Any]], event.results)

    actual_sql_clean = clean_query_for_eval(
        actual_generated_sql,
        keep_distinct=True,
    )
    expected_sql_clean = clean_query_for_eval(
        expected,
        keep_distinct=True,
    )

    print(f"Raw agent response: {raw_agent_response}")
    print(f"Raw agent response type: {type(raw_agent_response)} ")

    # Process the results into ExampleResult
    processed = ExampleResult(
        expected_sql_result=expected_sql_result,
        agent_response=raw_agent_response,
        actual_sql_query=actual_sql_clean,
        expected_sql_query=expected_sql_clean,
        actual_sql_result=actual_sql_result,
        is_valid_sql_result=is_valid_sql_result,
    )
    logger.info("post processing completed")
    return processed

async def resolver_factory(config: AgentConfig) -> ResourceResolver:
    # Load the query engine tool
    query_engine_tool = await create_default_query_engine_tool(config)

    logger.debug("Loading client")

    # We pass in the API key directly to the Phoenix client but it's likely
    # ignored. See oso_agent/util/config.py 
    logger.debug("Uploading dataset")

    # check if specific evals have been defined
    oso_mcp_client = OsoMcpClient(config.oso_mcp_url)

    resolver = ResourceResolver.from_resources(
        query_engine_tool=query_engine_tool,
        oso_mcp_client=oso_mcp_client,
        keep_distinct=True,
        agent_name=config.agent_name,
        agent_config=config,
        llm=create_llm(config),
    )
    return resolver


async def text2sql_experiment(
    config: AgentConfig, _registry: AgentRegistry, _raw_options: dict[str, t.Any]
):
    logger.info(f"Running text2sql experiment with: {config.model_dump_json()}") 
    
    api_key = config.arize_phoenix_api_key.get_secret_value()
    phoenix_client = px.Client(
        endpoint=config.arize_phoenix_base_url,
        headers={
            "api_key": api_key,
        },
    )

    example_ids = _raw_options.get("example_ids")
    dataset_name = (
        "local_run_text2sql_experiment" if example_ids else config.eval_dataset_text2sql
    )
    dataset = upload_dataset(
        phoenix_client, TEXT2SQL_DATASET, dataset_name, config, example_ids
    )

    logger.debug("Creating Oso MCP client")
    # workflow = TextI2SQLExperimentWorkflow(oso_mcp_client=oso_mcp_client, keep_distinct=True)

    async def clean_result(
        output: dict[str, t.Any], metadata: dict[str, t.Any], post_processed: str
    ) -> EvaluationResult:
        """Clean the result for evaluation."""
        return EvaluationResult(
            score=1.0,
            label="clean_result",
            explanation="The result has been cleaned and is ready for evaluation.",
        )

    logger.debug("Running experiment")

    runner = ExperimentRunner(
        config=config,
        resolver_factory=resolver_factory,
        concurrent_evaluators=10,
        concurrent_runs=1,
    )
    runner.add_evaluator(check_valid_sql)
    runner.add_evaluator(check_valid_sql_result)
    runner.add_evaluator(sql_query_type_similarity)
    runner.add_evaluator(sql_oso_models_used_similarity)
    runner.add_evaluator(result_exact_match)
    runner.add_evaluator(result_fuzzy_match) 

    return await runner.run(
        dataset=dataset,
        workflow_cls=BasicText2SQL,
        experiment_name=EXPERIMENT_NAME,
        experiment_metadata={"agent_name": config.agent_name},
        post_process_result=post_process_result,
    )
