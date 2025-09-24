"""A generic LLM workflow that simply pipes out to the LLM and returns the result."""

import hashlib
import logging
import textwrap

from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.workflow import Context, StopEvent, step
from oso_agent.types.response import StrResponse
from oso_agent.util.responses import ensure_no_code_block
from oso_agent.workflows.common import GenericStartEvent

from ...resources import ResourceDependency
from ..base import StartingWorkflow

logger = logging.getLogger(__name__)


class NotebookStartEvent(GenericStartEvent):
    """Start event for Notebook workflows."""

    input: str
    response_language: str


class NotebookWorkflow(
    StartingWorkflow[NotebookStartEvent],
):
    """The workflow used to help users with writing SQL or Python code into
    Marimo notebooks based on their natural language requests."""

    llm: ResourceDependency[FunctionCallingLLM]
    event_cls = NotebookStartEvent

    @step
    async def handle_start_event(
        self, _ctx: Context, event: NotebookStartEvent
    ) -> StopEvent:
        """Handle the start event by initiating the QueryEngine workflow."""

        if not event.id:
            # Generate a unique ID for the event if not provided
            event.id = hashlib.sha1(event.input.encode()).hexdigest()
            logger.debug("No ID provided for event, generated ID: %s", event.id)

        logger.info(
            "Handling generic query with input query[%s]: %s",
            event.id,
            event.input,
        )

        response = self.llm.predict(
            PromptTemplate(
                textwrap.dedent("""
            You are a helpful assistant that helps users with writing sql or
            python code into marimo notebooks based on their natural language
            requests.
                                           
            You must only response with valid sql or python code. Include
            comments where appropriate to explain your code. 
                                           
            Any python code you write can use anything that might be available in a 
            jupyter notebook as well.
                                           
            - You MUST NOT format your response in markdown. Only return the code. 
            - You MUST NOT include `import marimo as mo` in your python code. It is implied.
            - You MUST NOT include any text outside of the code.

            Here is the user request: {input}
            """)
            ),
            input=event.input,
        )

        # Remove markdown style code blocks if present
        response = ensure_no_code_block(response)

        return StopEvent(
            result=StrResponse(blob=response),
        )
