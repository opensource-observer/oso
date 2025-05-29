
from typing import List, Literal
from pydantic import BaseModel
from typing_extensions import TypedDict

# proposing a p0, p1, p2 priority system, where: 
# p0 = critical, p1 = important, p2 = nice to have

ExamplePriority = Literal["p0", "p1", "p2"]
ExampleDifficulty = Literal["easy", "medium", "hard"]
ExampleQueryType = Literal["filter", "aggregation", "join", "time-series", "derived metric", "sort / limit",  "subquery / cte"]
ExampleQueryDomain = Literal["github", "timeseries", "metrics", "directory", "blockchain", "funding"]

class ExampleInput(TypedDict):
    question: str

class ExampleOutput(TypedDict):
    answer: str

class ExampleMetadata(TypedDict):
    priority: ExamplePriority
    difficulty: ExampleDifficulty
    query_type: List[ExampleQueryType]
    query_domain: List[ExampleQueryDomain]

class Example(BaseModel):
    input: ExampleInput
    output: ExampleOutput
    metadata: ExampleMetadata

ExampleList = List[Example]

def create_example(question: str, answer: str, priority: ExamplePriority, difficulty: ExampleDifficulty, query_type: List[ExampleQueryType], query_domain: List[ExampleQueryDomain]) -> Example:
    return Example(
        input=ExampleInput(question=question),
        output=ExampleOutput(answer=answer),
        metadata=ExampleMetadata(
            priority=priority,
            difficulty=difficulty,
            query_type=query_type,
            query_domain=query_domain
        )
    )