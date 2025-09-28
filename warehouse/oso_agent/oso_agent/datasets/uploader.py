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
    server_questions = {
        str(example.input[QUESTION_KEY]) for example in server_ds.examples.values()
    }
    diff_examples = ExampleList(
        examples=[
            example
            for example in code_examples.examples
            if str(example.input[QUESTION_KEY]) not in server_questions
        ]
    )
    return diff_examples


def upload_dataset(
    phoenix_client: px.Client,
    code_examples: ExampleList,
    dataset_name: str,
    config: AgentConfig,
    example_ids: Optional[List[str]] = None,
) -> Dataset:
    """
    Upload a dataset to the Phoenix server, appending new examples if they do not already exist.
    Args:
        phoenix_client (px.Client): The Phoenix client to interact with the server.
        dataset_name (str): The name of the dataset to upload.
        code_examples (ExampleList): The local code examples to upload.
    """

    logger.info(
        f"Starting dataset upload process for '{dataset_name}' with {len(code_examples.examples)} total examples"
    )

    is_subset_mode = example_ids is not None and len(example_ids) > 0

    if is_subset_mode:
        logger.info(f"Filtering dataset to specific example IDs: {example_ids}")
        selected_code_examples = ExampleList(
            examples=[
                ex
                for ex in code_examples.examples
                if example_ids is not None and ex.metadata["id"] in example_ids
            ]
        )
        if not selected_code_examples.examples:
            raise ValueError(f"No examples matched IDs {example_ids}")
        logger.info(
            f"Selected {len(selected_code_examples.examples)} examples from filter"
        )
    else:
        selected_code_examples = code_examples
        logger.info(f"Using all {len(selected_code_examples.examples)} examples")

    dataset = Dataset("", "")  # for linter
    existing = False
    # first check to see if the dataset already exists
    logger.info(f"Checking if dataset '{dataset_name}' already exists")
    try:
        dataset = phoenix_client.get_dataset(name=dataset_name)
        existing = True
        logger.info(
            f"Found existing dataset '{dataset_name}' with {len(dataset.examples)} examples"
        )

        # if it does and we aren't running on a subset, diff and append
        if not is_subset_mode:
            logger.info(
                "Running in full dataset mode - will append new examples if any"
            )
            diff = diff_datasets(dataset, selected_code_examples)
            logger.info(
                f"Found {len(diff.examples)} new examples to append to dataset '{dataset_name}'"
            )
            if len(diff) > 0:
                logger.info(
                    f"Appending {len(diff.examples)} new examples to existing dataset"
                )
                dataset = phoenix_client.append_to_dataset(
                    dataset_name=dataset_name,
                    inputs=[ex.input for ex in diff.examples],
                    outputs=[ex.output for ex in diff.examples],
                    metadata=[ex.metadata for ex in diff.examples],
                )
            else:
                logger.info("No new examples to append - dataset is already up to date")
        # otherwise we need to delete the existing dataset
        else:
            logger.warning(
                f"DESTRUCTIVE OPERATION: Running in subset mode with example_ids={example_ids}"
            )
            logger.warning(
                f"This will DELETE the existing dataset '{dataset_name}' and ALL associated experiments!"
            )
            logger.warning(
                f"Existing dataset has {len(dataset.examples)} examples and may have experiments attached"
            )
            delete_phoenix_dataset(
                config.arize_phoenix_base_url,
                dataset.id,
                config.arize_phoenix_api_key.get_secret_value(),
            )
            # Reset this value because we just deleted the dataset
            existing = False
            logger.info(
                f"Deleted existing dataset '{dataset_name}' - will create new one with {len(selected_code_examples.examples)} examples"
            )

    except ValueError as e:
        if dataset_name not in str(e):
            logger.warning(f"Unknown error during dataset lookup: {e}")
            raise e
        else:
            logger.info(f"Dataset '{dataset_name}' not found, will create a new one")

    if not existing:
        logger.info(
            f"Creating new dataset '{dataset_name}' with {len(selected_code_examples.examples)} examples"
        )
        dataset = phoenix_client.upload_dataset(
            dataset_name=dataset_name,
            inputs=[ex.input for ex in selected_code_examples.examples],
            outputs=[ex.output for ex in selected_code_examples.examples],
            metadata=[ex.metadata for ex in selected_code_examples.examples],
        )
        logger.info(
            f"Successfully created dataset '{dataset_name}' with ID: {dataset.id}"
        )
    else:
        logger.info(f"Using existing dataset '{dataset_name}' with ID: {dataset.id}")

    # TODO: We need a better way to track changes to the dataset
    # We currently only upload examples with new questions,
    # but we don't track changes to answers or metadata.
    logger.info(
        f"Dataset upload completed for '{dataset_name}' - final dataset has {len(dataset.examples)} examples"
    )
    return dataset
