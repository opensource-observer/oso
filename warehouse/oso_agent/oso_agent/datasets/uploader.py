
import phoenix as px
from phoenix.experiments.types import Dataset

from ..types.datasets import ExampleList

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
    diff_examples = [
        example for example in code_examples if str(example.input[QUESTION_KEY]) not in server_questions
    ]
    return diff_examples

def upload_dataset(phoenix_client: px.Client, dataset_name: str, code_examples: ExampleList) -> Dataset:
    """
    Upload a dataset to the Phoenix server, appending new examples if they do not already exist.
    Args:
        phoenix_client (px.Client): The Phoenix client to interact with the server.
        dataset_name (str): The name of the dataset to upload.
        code_examples (ExampleList): The local code examples to upload.
    """
    dataset = phoenix_client.get_dataset(name=dataset_name)
    diffset = diff_datasets(dataset, code_examples)
    # TODO: We need a better way to track changes to the dataset
    # We currently only upload examples with new questions,
    # but we don't track changes to answers or metadata.
    if len(diffset) > 0:
        #dataset = phoenix_client.upload_dataset(
        dataset = phoenix_client.append_to_dataset(
            dataset_name=dataset_name,
            inputs=list(map(lambda x: x.input, diffset)),
            outputs=list(map(lambda x: x.output, diffset)),
            metadata=list(map(lambda x: x.metadata, diffset)),
        )
    return dataset