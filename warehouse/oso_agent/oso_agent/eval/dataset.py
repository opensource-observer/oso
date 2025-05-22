import asyncio

import nest_asyncio
import phoenix as px
from oso_agent.agent.agent import Agent
from oso_agent.eval.config import EvalConfig
from phoenix.experiments import run_experiment
from phoenix.experiments.evaluators import ContainsAnyKeyword
from phoenix.experiments.types import Example

nest_asyncio.apply()
contains_keyword = ContainsAnyKeyword(keywords=["UPDATE", "SELECT"])

async def main():
  config = EvalConfig()
  agent = await Agent.create(config)
  phoenix_client = px.Client()
  dataset = phoenix_client.get_dataset(
    name="test",
  )
  print(dataset.as_dataframe().to_dict())

  async def task(example: Example) -> str:
    print(f"Example: {example}")
    question = str(example.input["question"])
    print(f"Question: {question}")
    response = await agent.run(question)
    print(f"Response: {response}")
    return response

  experiment = run_experiment(
      dataset,
      task,
      experiment_name="initial-experiment",
      evaluators=[contains_keyword],
  )
  print(experiment)

asyncio.run(main())