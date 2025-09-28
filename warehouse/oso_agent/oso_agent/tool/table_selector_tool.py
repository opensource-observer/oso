"""
Tool for selecting relevant tables/models from the semantic registry for a specific query.
"""

import logging
from functools import partial

from llama_index.core import PromptTemplate
from llama_index.core.base.response.schema import Response
from llama_index.core.llms import LLM
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TableSelectionResponse(BaseModel):
    """Response containing selected models for a query."""

    selected_models: list[str] = Field(
        description="List of model names that are relevant to the query"
    )
    reasoning: str = Field(
        description="Brief explanation of why these models were selected"
    )


TABLE_SELECTION_PROMPT = """
TASK: Analyze a natural language query and select only the relevant tables/models from the semantic registry.

# QUERY TO ANALYZE
{natural_language_query}

# AVAILABLE MODELS IN REGISTRY
{available_models}

# SELECTION RULES
- Select ONLY models directly relevant to answering the query
- Prefer fewer models over more (be selective, not comprehensive)  
- Consider relationships: if querying projects, you may need collections
- Common patterns:
  - Projects queries: projects_v1, projects_by_collection_v1, collections_v1
  - Metrics queries: Add timeseries_metrics_by_project_v0, key_metrics_by_project_v0, metrics_v0
  - GitHub data: Add repositories_v0, int_events__github
  - Blockchain data: Add int_events_daily__blockchain, contracts_v0
  - Funding data: Add int_events_daily__funding
  - Dependencies: Add sboms_v0

Select 2-5 models maximum. Focus on core tables needed for the specific query.

Return the selected models and brief reasoning.
"""


async def _select_relevant_tables(
    natural_language_query: str,
    *,
    llm: LLM,
    available_models: str,
) -> Response:
    """
    Select relevant tables/models for a semantic query.

    Args:
        natural_language_query: The user's natural language query
        llm: The language model instance to use for selection
        available_models: String listing available models in the registry

    Returns:
        Response object containing the selected models
    """
    prompt_template = PromptTemplate(TABLE_SELECTION_PROMPT)

    structured_llm = llm.as_structured_llm(TableSelectionResponse)

    structured_response_str = await structured_llm.apredict(
        prompt_template,
        natural_language_query=natural_language_query,
        available_models=available_models,
    )

    structured_response = TableSelectionResponse.model_validate_json(
        structured_response_str
    )

    logger.info(
        "Selected %d models for query '%s': %s",
        len(structured_response.selected_models),
        natural_language_query,
        ", ".join(structured_response.selected_models),
    )
    logger.debug("Selection reasoning: %s", structured_response.reasoning)

    return Response(
        response=f"Selected models: {', '.join(structured_response.selected_models)}",
        metadata={"table_selection": structured_response},
    )


def create_table_selector_tool(llm: LLM, available_models: str) -> FunctionTool:
    """
    Factory function to create an instance of the TableSelectorTool.

    Args:
        llm: The language model instance to use for table selection
        available_models: String describing available models in the registry

    Returns:
        FunctionTool instance configured for table selection
    """
    tool_fn = partial(
        _select_relevant_tables,
        llm=llm,
        available_models=available_models,
    )

    return FunctionTool.from_defaults(
        async_fn=tool_fn,
        name="table_selector_tool",
        description="Selects relevant tables/models from the semantic registry for a specific query.",
    )
