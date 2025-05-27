
import json
from typing import Any, Dict

import nest_asyncio
import phoenix as px
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from phoenix.experiments import run_experiment
from phoenix.experiments.evaluators import ContainsAnyKeyword
from phoenix.experiments.types import Example

from ..tool.oso_mcp import create_oso_mcp_tools
from ..util.config import AgentConfig
from ..util.jaccard import jaccard_similarity_str

EXPERIMENT_NAME = "text2sql-experiment"
try:
    nest_asyncio.apply()
except ValueError:
    pass

async def text2sql_experiment(config: AgentConfig, agent: BaseWorkflowAgent):
  print("Running text2sql experiment with:", config)
  phoenix_client = px.Client()
  dataset = phoenix_client.get_dataset(
    name=config.eval_dataset_text2sql,
  )

  async def task(example: Example) -> str:
    #print(f"Example: {example}")
    question = str(example.input["question"])
    #print(f"Question: {question}")
    #expected = str(example.output["answer"])
    #print(f"Expected: {expected}")
    response = await agent.run(question)
    response_dict = json.loads(str(response))
    #print(f"Response: {response_dict}")
    response_query = response_dict["query"]
    #print(f"Response Query: {response_query}")
    return response_query

  contains_select = ContainsAnyKeyword(keywords=["SELECT"])

  def sql_query_similarity(output: str, expected: Dict[str, Any]) -> float:
      """Evaluate the similarity between the output and expected SQL query using Jaccard similarity."""
      #print(f"Output: {output}")
      #print(f"Expected: {expected["answer"]}")
      return jaccard_similarity_str(output, expected["answer"])

  mcp_tools = await create_oso_mcp_tools(config, ["query_oso"])
  query_tool = mcp_tools[0]

  def sql_result_similarity(output: str, expected: Dict[str, Any]) -> float:
      """Evaluate the similarity between results post-query"""
      expected_response = query_tool.call(sql=expected["answer"])
      expected_str = expected_response.content
      #print(f"Expected Str: {expected_str}")

      output_response = query_tool.call(sql=output)
      output_str = output_response.content
      #print(f"Output Response: {output_str}")

      return jaccard_similarity_str(output_str, expected_str)

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
  )
  return experiment
