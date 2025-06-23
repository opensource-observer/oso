import pytest
from llama_index.core.workflow import Event, StartEvent, StopEvent, step

from .base import MixableWorkflow, ResourceDependency, ResourceResolver


class CustomEvent(Event):
    test_value: str


@pytest.mark.asyncio
async def test_mixable_workflow():
    class Resource1Workflow(MixableWorkflow):
        resource1: ResourceDependency[str]
        with_default: ResourceDependency[str] = ResourceDependency(default_factory=lambda: "default_value")

        @step
        async def handle_start(self, ev: StartEvent) -> CustomEvent:
            assert self.with_default == "default_value", "Default value should be set correctly"
            return CustomEvent(test_value=self.resource1)

    class Resource2Workflow(MixableWorkflow):
        resource2: ResourceDependency[str]
        event_log: ResourceDependency[list[str]]

        @step
        async def log_start(self, ev: StartEvent) -> None:
            self.event_log.append("Logging the start event")

        @step
        async def handle_custom_event(self, ev: CustomEvent) -> StopEvent:
            return StopEvent(result=f"{ev.test_value} {self.resource2}")

    class MixedWorkflows(Resource1Workflow, Resource2Workflow):
        pass

    event_log: list[str] = []
    resolver = ResourceResolver.from_resources(
        resource1="test1", resource2="test2", event_log=event_log
    )

    wk = MixedWorkflows(resolver=resolver)
    handler = wk.run(stepwise=True, hi="hi")

    expected_events = [CustomEvent, StopEvent]
    expected_events.reverse()

    events = await handler.run_step()
    while events:
        expected_event = expected_events.pop()
        for ev in events:
            assert handler.ctx is not None, "Context should be set in the handler"
            assert isinstance(
                ev, expected_event
            ), f"Expected {expected_event.__name__}, got {ev.__class__.__name__}"
            handler.ctx.send_event(ev)
        events = await handler.run_step()
    assert handler.result() == "test1 test2"
    assert len(event_log) == 1
