
import json

import nest_asyncio
import phoenix as px
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from phoenix.experiments import run_experiment
from phoenix.experiments.evaluators import ContainsAnyKeyword
from phoenix.experiments.types import Example

from ..util.config import AgentConfig

EXPERIMENT_NAME = "text2sql-experiment"

nest_asyncio.apply()
contains_keyword = ContainsAnyKeyword(keywords=["SELECT"])

async def text2sql_experiment(config: AgentConfig, agent: BaseWorkflowAgent):
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

  experiment = run_experiment(
      dataset,
      task,
      experiment_name=EXPERIMENT_NAME,
      evaluators=[contains_keyword],
  )
  return experiment
