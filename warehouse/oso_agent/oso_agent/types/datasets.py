import re
from typing import List, Literal, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

from ..util.query import (
    ExampleQueryType,
    determine_query_type,
    determine_sql_models_used,
)

##### Text2SQL #####

ExamplePriority = Literal["P0", "P1", "P2"] # P0 = critical, P1 = important, P2 = nice to have
ExampleDifficulty = Literal["easy", "medium", "hard"]
ExampleSQLModelsUsed = [] # if this is something we want to enforce we can call models_v0 and ensure that the models used in the example are in this list
ExampleQuestionCategories = Literal[
    "project_or_collection",        # Project or collection membership, counts, or listing
    "repo_or_package_metrics",      # GitHub, NPM, or artifact-level stats (stars, forks, releases, etc.)
    "funding_and_grants",           # Funding events, grants, awarded amounts, or related filters
    "developer_activity",           # Developer, contributor, or commit activity and related counts
    "blockchain_activity",          # Chain-specific metrics: transactions, gas usage, TVL, or contract calls
    "dependencies_and_software",    # Dependency or package analysis (number, growth, associations)
    "pr_and_issue_tracking",        # Pull requests, issues, merge rates, or related comparisons
    "comparative_or_trend_analysis" # Rankings, temporal trends, cross-metric or composite conditions
]

class ExampleInput(TypedDict):
    question: str

class ExampleOutput(TypedDict):
    answer: str

class ExampleMetadata(TypedDict):
    priority: ExamplePriority
    difficulty: ExampleDifficulty
    query_type: List[ExampleQueryType]
    sql_models_used: List[str]
    question_categories: List[ExampleQuestionCategories]
    real_user_question: bool

class Example(BaseModel):
    id: str
    input: ExampleInput
    output: ExampleOutput
    metadata: ExampleMetadata

class ExampleList(BaseModel):
    examples: List[Example]

    def __init__(self, examples: List[Example]):
        # validate ids
        seen_ids = set()
        for example in examples:
            if example.id in seen_ids:
                raise ValueError(f"Duplicate example ID found: {example.id!r}") # update this
            seen_ids.add(example.id)
        super().__init__(examples=examples)

    def __len__(self) -> int:
        return len(self.examples)


def create_text2sql_example(id: str, question: str, answer_query: str, priority: ExamplePriority, difficulty: ExampleDifficulty, question_categories: List[ExampleQuestionCategories], real_user_question: bool) -> Example:
    # validate passed id
    if not re.fullmatch(r"[1-9]\d*", id):
        raise ValueError(f"Invalid example id {id!r}: must be a string representing a positive integer.")
    
    return Example(
        id=id,
        input=ExampleInput(question=question),
        output=ExampleOutput(answer=answer_query),
        metadata=ExampleMetadata(
            priority=priority,
            difficulty=difficulty,
            query_type=determine_query_type(answer_query),
            sql_models_used=determine_sql_models_used(answer_query),
            question_categories=question_categories,
            real_user_question=real_user_question
        )
    )

###### Backlog Questions #####

class BacklogQuestion(BaseModel):
    question: str                               
    real_user_question: bool  
    answer: Optional[str] = None                             
    priority: Optional[ExamplePriority] = None 
    difficulty: Optional[ExampleDifficulty] = None
    question_categories: Optional[List[ExampleQuestionCategories]] = None
    notes: Optional[str] = None     

def create_backlog_question(question: str, real_user_question: bool, answer: Optional[str] = None, priority: Optional[ExamplePriority] = None, difficulty: Optional[ExampleDifficulty] = None, question_categories: Optional[List[ExampleQuestionCategories]] = None, notes: Optional[str] = None) -> BacklogQuestion:
    return BacklogQuestion(
        question=question,
        real_user_question=real_user_question,
        answer=answer,
        priority=priority,
        difficulty=difficulty,
        question_categories=question_categories,
        notes=notes
    )