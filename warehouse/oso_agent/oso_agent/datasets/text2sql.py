from typing import List

from ..types.datasets import Example, create_example

TEXT2SQL_DATASET_DESCRIPTION = "Text2SQL dataset for evaluating SQL query generation from natural language questions."
TEXT2SQL_DATASET: List[Example] = [
    create_example(
        question="How many projects are in the 'optimism' collection?",
        answer="SELECT COUNT(DISTINCT pbc.project_id) AS num_projects FROM projects_by_collection_v1 AS pbc JOIN collections_v1 AS c ON pbc.collection_id = c.collection_id WHERE c.display_name LIKE 'optimism'",
        priority="medium",
        difficulty="easy",
        query_type=["aggregation", "filter"],
        query_domain=["directory"]
    ),
]