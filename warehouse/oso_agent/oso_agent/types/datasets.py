from typing import List, Literal, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

import sqlglot
from sqlglot import expressions as exp
_DIALECT = "trino"

##### Text2SQL #####

ExamplePriority = Literal["P0", "P1", "P2"] # P0 = critical, P1 = important, P2 = nice to have
ExampleDifficulty = Literal["easy", "medium", "hard"]
ExampleQueryType = Literal[
    "aggregation",     
    "filter",         
    "join",            
    "group_by",        
    "order_by",        
    "window_function",
    "time_series",    
    "limit",         
    "union",           
    "case_when",      
    "array",           
    "cte",             
    "other"            
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

def determine_query_type(query: str, dialect: str = _DIALECT) -> List[ExampleQueryType]:
    try:
        tree = sqlglot.parse_one(query, dialect=dialect)
    except sqlglot.errors.ParseError:
        # if the sql cannot be parsed fall back to 'other'
        return ["other"]

    types: List[ExampleQueryType] = []

    if any(node.is_aggregate for node in tree.walk()):
        types.append("aggregation")

    if tree.find(exp.Where):
        types.append("filter")

    if tree.find(exp.Join):
        types.append("join")

    if tree.find(exp.Group):
        types.append("group_by")

    if tree.find(exp.Order):
        types.append("order_by")

    if tree.find(exp.Limit):
        types.append("limit")

    if tree.find(exp.With):
        types.append("cte")

    if tree.find(exp.Union):
        types.append("union")

    if tree.find(exp.Window):
        types.append("window_function")

    if tree.find(exp.Case):
        types.append("case_when")

    if tree.find(exp.ArrayAgg) or tree.find(exp.Array):
        types.append("array")

    time_funcs = {
        "date", "date_add", "date_diff", "date_trunc", "extract",
        "time", "timestamp", "to_unixtime", "from_unixtime", "interval"
    }
    for func in tree.find_all(exp.Func):
        if func.name.lower() in time_funcs:
            types.append("time_series")
            break

    if not types:
        types.append("other")

    return types


def determine_sql_models_used(query: str, dialect: str = _DIALECT) -> List[str]:
    try:
        tree = sqlglot.parse_one(query, dialect=dialect)
    except sqlglot.errors.ParseError:
        return []

    tables = list(set([tbl.name for tbl in tree.find_all(exp.Table)]))
    return tables


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