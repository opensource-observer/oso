from dataclasses import dataclass
from llama_index.core.workflow import Event
from ..types.response import WrappedResponse
from .base import MixableWorkflow


@dataclass
class EvalWorkflowResult:
    """A dataclass to hold the result of an evaluation workflow."""
    events: list[Event]
    final_result: WrappedResponse | None = None


class EvalWorkflow(MixableWorkflow):
    """A workflow that runs a workflow and returns the entire history of events
    for introspection."""

    async def run_for_evals(self, *args, **kwargs) -> EvalWorkflowResult:
        """Run the workflow and return the result."""
        events = []
        final_result = None
        async for event in self.run_events_iter(*args, **kwargs):
            #print("asfafaf")
            #print(type(event))
            if isinstance(event, Event):
                events.append(event)
            elif isinstance(event, WrappedResponse):
                final_result = event

        return EvalWorkflowResult(events=events, final_result=final_result)


