import logging
from typing import List, Optional

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
    diff_examples = ExampleList(examples=[
        example for example in code_examples.examples if str(example.input[QUESTION_KEY]) not in server_questions
    ])
    return diff_examples

def upload_dataset(phoenix_client: px.Client, code_examples: ExampleList, dataset_name: str, config: AgentConfig, example_ids: Optional[List[str]] = None) -> Dataset:
    """
    Upload a dataset to the Phoenix server, appending new examples if they do not already exist.
    Args:
        phoenix_client (px.Client): The Phoenix client to interact with the server.
        dataset_name (str): The name of the dataset to upload.
        code_examples (ExampleList): The local code examples to upload.
    """

    if example_ids and len(example_ids) > 0:
        selected_code_examples = ExampleList(
            examples=[ex for ex in code_examples.examples if ex.metadata['id'] in example_ids]
        )
        if not selected_code_examples.examples:
            raise ValueError(f"No examples matched IDs {example_ids}")
    else:
        selected_code_examples = code_examples

    
    dataset = Dataset("", "")  # for linter
    appended = False
    # first check to see if the dataset already exists
    try:
        dataset = phoenix_client.get_dataset(name=dataset_name)

        # if it does and we aren't running on a subset, diff and append
        if example_ids is None:
            diff = diff_datasets(dataset, selected_code_examples)
            if len(diff) > 0:
                dataset = phoenix_client.append_to_dataset(
                    dataset_name=dataset_name,
                    inputs=[ex.input for ex in diff.examples],
                    outputs=[ex.output for ex in diff.examples],
                    metadata=[ex.metadata for ex in diff.examples],
                )
                appended = True
        # otherwise we need to delete the existing dataset
        else:  
            delete_phoenix_dataset(
                config.arize_phoenix_base_url,
                dataset.id,
                config.arize_phoenix_api_key.get_secret_value()
            )       

    except ValueError as e:
        if dataset_name not in str(e):
            logger.warning(f"Unknown error. Possibly '{dataset_name}' not found")
            raise e
        else:
            logger.info(f"Dataset '{dataset_name}' not found, creating a new one.")
    
    if not appended:
        dataset = phoenix_client.upload_dataset(
            dataset_name=dataset_name,
            inputs=[ex.input for ex in selected_code_examples.examples],
            outputs=[ex.output for ex in selected_code_examples.examples],
            metadata=[ex.metadata for ex in selected_code_examples.examples],
        )
            
    # TODO: We need a better way to track changes to the dataset
    # We currently only upload examples with new questions,
    # but we don't track changes to answers or metadata. 
    return dataset
