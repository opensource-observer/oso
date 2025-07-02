import logging
import typing as t

from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.types import BaseOutputParser
from llama_index.core.workflow import Context, StartEvent, StopEvent, step
from oso_agent.resources import DefaultResourceResolver
from oso_agent.tool.llm import create_llm
from oso_agent.types.response import AnyResponse, ErrorResponse
from oso_agent.util.config import AgentConfig
from oso_agent.workflows.base import MixableWorkflow, ResourceDependency
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class PydanticOutputParser(BaseOutputParser):
    def __init__(self, model_cls):
        self.model_cls = model_cls

    def parse(self, output: str):
        # parse output string as JSON and validate with Pydantic
        return self.model_cls.model_validate_json(output)

class LLMStructuredOutputWorkflow(MixableWorkflow):
    """
    A workflow that takes a prompt and a pydantic structured output class, sends the prompt to an LLM,
    parses the result as the pydantic class, and returns it.
    """
    config: ResourceDependency[AgentConfig]
    structured_output_class: ResourceDependency[t.Callable[..., BaseModel]]
    llm: ResourceDependency[FunctionCallingLLM]

    @step
    async def handle_prompt(self, ctx: Context, event: StartEvent) -> StopEvent:
        """
        Handle the start event: send the prompt to the LLM and parse the result as the structured output class.
        """
        prompt_str = getattr(event, "input", None)
        if not prompt_str:
            logger.error("No prompt provided in StartEvent.")
            return StopEvent(result=ErrorResponse(message="No prompt provided."))

        structured_output_class = self.structured_output_class
        prompt = PromptTemplate(
            template=prompt_str,    
            output_parser=PydanticOutputParser(structured_output_class),
            prompt_type="structured_output",
        )

        try:
            llm = self.llm
            logger.info(f"Sending prompt to LLM: {prompt}")
            llm_response = await llm.astructured_predict(output_cls=structured_output_class, prompt=prompt)
            logger.info(f"LLM response: {llm_response}")
            return StopEvent(result=AnyResponse(raw=llm_response))
        
        except ValidationError as ve:
            logger.error(f"Failed to parse LLM output: {ve}")
            return StopEvent(result=ErrorResponse(message="Failed to parse LLM output.", details=str(ve)))
        
        except Exception as e:
            logger.error(f"Error in LLMStructuredOutputWorkflow: {e}")
            return StopEvent(result=ErrorResponse(message=str(e)))

def create_llm_structured_output_workflow(
    config: AgentConfig,
    structured_output_class: t.Type[BaseModel],
) -> LLMStructuredOutputWorkflow:
    """
    Factory to create the LLMStructuredOutputWorkflow with the required resources.
    """
    llm = create_llm(config)
    resolver = DefaultResourceResolver.from_resources(
        config=config,
        llm=llm,
        structured_output_class=structured_output_class,
    )
    return LLMStructuredOutputWorkflow(resolver=resolver) 