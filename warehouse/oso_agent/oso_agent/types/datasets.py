import re
from typing import List, Literal, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

##### Text2SQL #####

ExamplePriority = Literal["P0", "P1", "P2"] # P0 = critical, P1 = important, P2 = nice to have
ExampleDifficulty = Literal["easy", "medium", "hard"]
ExampleQueryType = Literal[
    "aggregation",     # COUNT, SUM, AVG, MIN, MAX, etc.
    "filter",          # WHERE clauses
    "join",            # JOINs between tables
    "group_by",        # GROUP BY
    "order_by",        # ORDER BY, sorting
    "subquery",        # Subquery usage
    "window_function", # OVER(), ROW_NUMBER(), etc.
    "time_series",     # Date filtering, time bucketing
    "limit",           # LIMIT clauses
    "union",           # UNION, UNION ALL
    "case_when",       # CASE WHEN logic
    "array",           # ARRAY_AGG, etc.
    "cte",             # WITH ... AS (...)
    "other"            # Catch-all
]
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
    input: ExampleInput
    output: ExampleOutput
    metadata: ExampleMetadata

ExampleList = List[Example]

def determine_query_type(query: str) -> List[ExampleQueryType]:
    types = []
    q = query.lower()
    if re.search(r"\b(sum|count|avg|min|max)\b", q):
        types.append("aggregation")
    if "where" in q:
        types.append("filter")
    if "join" in q:
        types.append("join")
    if "group by" in q:
        types.append("group_by")
    if "order by" in q:
        types.append("order_by")
    if "limit" in q:
        types.append("limit")
    if "with " in q:
        types.append("cte")
    if "union" in q:
        types.append("union")
    if "case when" in q or "case\nwhen" in q:
        types.append("case_when")
    if "array_" in q:
        types.append("array")
    if re.search(r"\b(row_number|over\s*\()", q):
        types.append("window_function")
    if re.search(r"\bdate|extract|interval|bucket|time\b", q):
        types.append("time_series")
    if not types:
        types.append("other")
    return types

def determine_sql_models_used(query: str) -> List[str]:
    tables = re.findall(r'(?:from|join)\s+([a-zA-Z0-9_.]+)', query, flags=re.IGNORECASE)
    oso_tables = [t[4:] for t in tables if t.startswith("oso.")]
    return sorted(set(oso_tables))

def create_text2sql_example(question: str, answer_query: str, priority: ExamplePriority, difficulty: ExampleDifficulty, question_categories: List[ExampleQuestionCategories], real_user_question: bool) -> Example:
    return Example(
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