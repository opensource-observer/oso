import logging
from typing import List

import phoenix as px
from phoenix.experiments.types import Dataset

from ..types.datasets import ExampleList
from ..util.config import AgentConfig
from ..util.datasets import delete_phoenix_dataset

logger = logging.getLogger(__name__)


QUESTION_KEY = "question"

def diff_datasets(server_ds: Dataset, code_examples: ExampleList) -> ExampleList:
    """
    Compare the server dataset with the local code examples and return the differences.
    
    Args:
        server_ds (Dataset): The dataset from the server.
        code_examples (ExampleList): The local code examples to compare against.
    
    Returns:
        ExampleList: A list of examples that are in the local code examples but not in the server dataset.
    """
    server_questions = {str(example.input[QUESTION_KEY]) for example in server_ds.examples.values()}
    diff_examples = ExampleList([
        example for example in code_examples.examples if str(example.input[QUESTION_KEY]) not in server_questions
    ])
    return diff_examples

def upload_dataset(phoenix_client: px.Client, dataset_name: str, code_examples: ExampleList) -> Dataset:
    """
    Upload a dataset to the Phoenix server, appending new examples if they do not already exist.
    Args:
        phoenix_client (px.Client): The Phoenix client to interact with the server.
        dataset_name (str): The name of the dataset to upload.
        code_examples (ExampleList): The local code examples to upload.
    """
    try:
        dataset = phoenix_client.get_dataset(name=dataset_name)
        diffset = diff_datasets(dataset, code_examples)
        if len(diffset) > 0:
            #dataset = phoenix_client.upload_dataset(
                dataset = phoenix_client.append_to_dataset(
                    dataset_name=dataset_name,
                    inputs=[ex.input for ex in diffset.examples],
                    outputs=[ex.output for ex in diffset.examples],
                    metadata=[ex.metadata for ex in diffset.examples],
                )
    except ValueError as e:
        if dataset_name not in str(e):
            logger.warning(f"Unknown error. Possibly '{dataset_name}' not found")
            raise e
        else:
            logger.info(f"Dataset '{dataset_name}' not found, creating a new one.")
            dataset = phoenix_client.upload_dataset(
                dataset_name=dataset_name,
                inputs=[ex.input for ex in code_examples.examples],
                outputs=[ex.output for ex in code_examples.examples],
                metadata=[ex.metadata for ex in code_examples.examples],
            )
            
    # TODO: We need a better way to track changes to the dataset
    # We currently only upload examples with new questions,
    # but we don't track changes to answers or metadata. 
    return dataset

def upload_specified_dataset(phoenix_client: px.Client, code_examples: ExampleList, eval_ids: List[str], config: AgentConfig, dataset_name: str = "local_run_text2sql_experiment") -> Dataset:
    """
    Same as `upload_dataset`, but restrict upload to the examples whose IDs appear in `eval_ids`.  Useful for ad-hoc local runs.
    Args:
        phoenix_client (px.Client): The Phoenix client to interact with the server.
        code_examples (ExampleList): The local code examples to upload.
    """

    # build the subset
    selected = ExampleList([ex for ex in code_examples.examples if ex.id in eval_ids])
    if not selected:
        raise ValueError(
            f"No examples matched IDs {eval_ids}. "
            "Check the list or load a different ExampleList."
        )

    # upload the dataset
    try:
        # clear any existing content within the dataset
        dataset = phoenix_client.get_dataset(name=dataset_name)

        # if we are here the dataset exists and we need to delete it
        base_url = config.arize_phoenix_base_url
        api_key = config.arize_phoenix_api_key.get_secret_value()
        delete_phoenix_dataset(base_url, dataset.id, api_key)

    except ValueError as e: # if we are here the dataset doesn't exist and a new one will be made
        if dataset_name not in str(e):
            logger.warning("Unexpected error while fetching dataset")
            raise
        logger.info(f"Dataset '{dataset_name}' not found, creating a new one")
 
    dataset = phoenix_client.upload_dataset(
        dataset_name=dataset_name,
        inputs=[ex.input for ex in selected.examples],
        outputs=[ex.output for ex in selected.examples],
        metadata=[ex.metadata for ex in selected.examples],
    )

    return dataset
