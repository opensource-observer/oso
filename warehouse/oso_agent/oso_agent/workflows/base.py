import asyncio
import inspect
import logging
import typing as t
import uuid

from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from llama_index.core.workflow.decorators import StepConfig
from llama_index.core.workflow.handler import WorkflowHandler
from llama_index.core.workflow.workflow import WorkflowMeta
from opentelemetry import trace
from oso_agent.agent.agent_registry import AgentRegistry
from oso_agent.types.response import AnyResponse, ResponseType
from oso_agent.util.config import AgentConfig
from oso_agent.workflows.types import ExceptionEvent

from ..types import ErrorResponse, WrappedResponse

ResponseWrapper = t.Callable[[t.Any], WrappedResponse]

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


V = t.TypeVar("V")

class ResolverEnabled(t.Protocol):
    resolver: "ResourceResolver"

    def resolve_resource(
        self, name: str, default_factory: t.Optional[t.Callable[[], t.Any]]
    ) -> t.Any: ...


class ResourceDependency(t.Generic[V]):
    def __init__(self, default_factory: t.Optional[t.Callable[[], V]] = None):
        """A descriptor for resource dependencies in a workflow."""
        self._default_factory = default_factory

    def __set_name__(self, _owner, name):
        self._name = name

    def __get__(self, obj: ResolverEnabled, owner: t.Any) -> V:
        return obj.resolve_resource(self._name, self._default_factory)

    def __set__(self, obj: t.Optional[object], value: V) -> None:
        raise AttributeError(
            f"Cannot set resource '{self._name}'. Resources are immutable after initialization."
        )
    
    def has_default_factory(self) -> bool:
        """Check if the resource has a default factory."""
        return self._default_factory is not None


class ResourceResolver:
    """A resolver for resources in a workflow using a service locator pattern)."""

    @classmethod
    def from_resources(cls, **kwargs: t.Any) -> "ResourceResolver":
        """Create a ResourceResolver from keyword arguments."""
        resolver = cls()
        for name, value in kwargs.items():
            resolver.add_resource(name, value)
        return resolver

    def __init__(self):
        self._resources: dict[str, t.Any] = {}

    def add_resource(self, name: str, resource: t.Any) -> None:
        self._resources[name] = resource

    def get_resource(self, name: str) -> t.Any:
        """Get a resource by name."""
        if name not in self._resources:
            raise KeyError(f"Resource '{name}' not found in resolver.")
        return self._resources[name]

    def validate_for_required_resources(
        self, resources_dict: dict[str, type]
    ) -> list[tuple[str, str]]:
        """Check if all resources in the dictionary are available in the resolver."""
        missing_resources: list[tuple[str, str]] = []
        for name, resource_type in resources_dict.items():
            if name not in self._resources:
                missing_resources.append((
                    name,
                    f"Resource '{name}' is missing from the resolver."
                ))
            elif not isinstance(self._resources[name], resource_type):
                missing_resources.append((
                    name,
                    f"Resource '{name}' is of type {type(self._resources[name])}, "
                    f"but should be {resource_type}.",
                ))
        return missing_resources
    
    def new_resolver(self, **additional_resources: t.Any) -> "ResourceResolver":
        """Extend the resolver with additional resources."""
        kwargs = {**self._resources, **additional_resources}
        return ResourceResolver.from_resources(**kwargs)


class WorkflowMixer(WorkflowMeta):
    def __new__(cls, name: str, bases: t.Tuple[type, ...], dct: t.Dict[str, t.Any]):
        """Ensure that annotated resource dependencies have a default value in dct"""

        required_resources: dict[str, type] = {}

        for base in bases:
            if base.__class__ != cls:
                if issubclass(base, Workflow):
                    # If the base class is a regular workflow, we can skip it
                    continue
                if not issubclass(base.__class__, WorkflowMixer):
                    # If the base class is a mixable workflow, we can skip it
                    raise TypeError(
                        f"Base class {base.__name__} is not a mixable workflow."
                    )
                raise TypeError(
                    f"Base class {base.__name__} is not a mixable workflow."
                )

            for attr_name, attr_type in base.__annotations__.items():
                if isinstance(attr_type, ResourceDependency):
                    args = getattr(attr_type, "__args__", None)
                    assert (
                        args is not None
                    ), "ResourceDependency must have type arguments."
                    if len(args) != 1:
                        raise TypeError(
                            f"ResourceDependency for {attr_name} must have exactly one type argument."
                        )
                    if attr_name in required_resources:
                        if required_resources[attr_name] != args[0]:
                            raise TypeError(
                                f"ResourceDependency for {attr_name} has conflicting types: "
                                f"{required_resources[attr_name]} and {args[0]}"
                            )
                    else:
                        typ = args[0]
                        required_resources[attr_name] = typ
                        if dct.get(attr_name) is None:
                            dct[attr_name] = ResourceDependency()

        for attr_name, attr_type in dct.get("__annotations__", {}).items():
            if t.get_origin(attr_type) == ResourceDependency:
                args = t.get_args(attr_type)
                assert args is not None, "ResourceDependency must have type arguments."
                if len(args) != 1:
                    raise TypeError(
                        f"ResourceDependency for {attr_name} must have exactly one type argument."
                    )
                if attr_name in required_resources:
                    if required_resources[attr_name] != args[0]:
                        raise TypeError(
                            f"ResourceDependency for {attr_name} has conflicting types: "
                            f"{required_resources[attr_name]} and {args[0]}"
                        )
                else:
                    typ = args[0]
                    required_resources[attr_name] = typ
                    if dct.get(attr_name) is None:
                        dct[attr_name] = ResourceDependency()

        # Automatically wrap all steps with an error handler
        for key, value in dct.items():
            if inspect.isfunction(value) and hasattr(value, "__step_config"):
                dct[key] = wrap_step_with_error_handler(value)

        cls._required_resources = required_resources

        return super().__new__(cls, name, bases, dct)
    
T = t.TypeVar("T")

def wrap_step_with_error_handler(func: t.Callable[..., t.Awaitable[T]]) -> t.Callable[..., t.Awaitable[T | ExceptionEvent]]:
    """Decorator to wrap an existing step function with an error handler."""
    step_config = t.cast(StepConfig, getattr(func, "__step_config", None))
    assert step_config is not None, "Function must be a step to use wrap_step_with_error_handler"

    # If the step _handles_ ExceptionEvent, we choose not to wrap it, as it is
    # supposed to handle exceptions after they've occurred
    if ExceptionEvent in step_config.accepted_events:
        return func
    
    # If the step already returns ExceptionEvent, we assume it has its own error handling
    if ExceptionEvent in step_config.return_types:
        return func

    async def error_handler(*args, **kwargs) -> T | ExceptionEvent:
        """Error handler for the step that wraps the response in a WrappedResponse."""
        try:
            response = await func(*args, **kwargs)
            return response
        except Exception as e:
            return ExceptionEvent(error=e)

    step_config.return_types.append(ExceptionEvent)
    error_handler.__step_config = step_config  # type: ignore[attr-defined]
    return error_handler


class MixableWorkflow(Workflow, metaclass=WorkflowMixer):
    """A MixableWorkflow is a workflow that can be mixed with other workflows
    all the steps in the workflow are mixable and can be used in other workflows
    to allow for decoupling of step processing.

    To allow for this the workflows use a dependency injection pattern similar
    to something like a server locator by annotating attributes with
    ResourceDependency.

    Additionally, this "mixable" workflow was made because composing workflows
    from workflows actually proved harder to introspect for evals. This flattens
    all of the steps into a single workflow by default and allows for the use of
    of the "stepwise" run style of llama_index workflows to iterate through each
    step.
    """

    def __init__(self, resolver: ResourceResolver, **kwargs: t.Any):
        super().__init__(**kwargs)
        self.resolver = resolver
        self._resolved_resources: dict[str, t.Any] = {}

        # Usually we shouldn't do much error handling in the constructor but the
        # metaclass necessitates that we validate the required resources
        # available at this point.

        missing_resources = resolver.validate_for_required_resources(
            self.__class__._required_resources
        )
        if missing_resources:
            errors: list[str] = []
            for name, error in missing_resources:
                if "missing" in error:
                    attr = getattr(self.__class__, name)
                    if isinstance(attr, ResourceDependency) and attr.has_default_factory():
                        # If the resource has a default factory, we can skip the error
                        continue
                errors.append(error)
            raise TypeError(
                f"Missing required resources for {self.__class__.__name__}: "
                + ", ".join(errors)
            )
        # for name, resource in self.__class__._required_resources.items():
        #     setattr(self, name, ResourceDependency())

    async def wrapped_run(self, *args, **kwargs) -> WrappedResponse:
        """Run the workflow with wrapped response."""
        handler = self.run(*args, **kwargs)
        with tracer.start_as_current_span("wrapped_run"):
            try:
                raw_response = await handler
            except Exception as e:
                return WrappedResponse(handler=handler, response=self._wrap_error(e))
            if not isinstance(raw_response, ResponseType):
                return WrappedResponse(
                    handler=handler,
                    response=self._wrap_error(
                        TypeError(
                            f"Expected response of type ResponseType, got {type(raw_response)}"
                        )
                    ),
                )
        return WrappedResponse(handler=handler, response=raw_response)

    def _wrap_error(self, error: Exception) -> ResponseType:
        """Wrap an error into a response."""
        response = ErrorResponse(
            message=str(error),
        )
        return response

    def resolve_resource(
        self, name: str, default_factory: t.Optional[t.Callable[[], t.Any]] = None
    ) -> t.Any:
        """Resolve a resource by name, using a default factory if provided."""

        # If the resource has already been resolved, return it
        resolved_resource = self._resolved_resources.get(name)
        if not resolved_resource:
            # Otherwise, get the resource from the resolver
            try:
                resolved_resource = self.resolver.get_resource(name)
            except KeyError as e:
                if default_factory is not None:
                    # If a default factory is provided, use it to create the resource and store that result
                    resource = default_factory()
                    resolved_resource = resource
                else:
                    raise e
        # Store the resolved resource for future use
        self._resolved_resources[name] = resolved_resource
        return resolved_resource
    
    async def run_events_iter(self, **kwargs) -> t.AsyncIterable[Event | WrappedResponse]:
        """Run the workflow and yield responses as they are produced."""

        run_id = str(uuid.uuid4())
        logger.debug(f"running workflow {self.__class__.__name__} with run_id: run[{run_id}]")

        with tracer.start_as_current_span("run_events_iter"):
            handler = self.run(stepwise=True, **kwargs)
            try:
                events = await self._wait_for_events(run_id, handler)
                logger.debug(f"initial events run[{run_id}]: {len(events or [])}")

                while events:
                    for event in events:
                        yield event
                        assert handler.ctx is not None, "Workflow handler context is not set."
                        handler.ctx.send_event(event)
                    events = await self._wait_for_events(run_id, handler)
                    logger.debug(f"next events run[{run_id}]: {len(events or [])}")

            except Exception as e:
                logger.error(f"error running workflow run[{run_id}]: {e}")
                yield WrappedResponse(handler=handler, response=self._wrap_error(e))
            try:
                yield self.ensure_wrapped_response(handler)
            except Exception as e:
                logger.error(f"error retrieving the final response for run[{run_id}]: {e}")
                yield WrappedResponse(handler=handler, response=self._wrap_error(e))

    async def _wait_for_events(self, run_id: str, handler: WorkflowHandler) -> t.List[Event]:
        """Wait for events to be produced by the workflow handler.

        This is made to be fairly robust against timeout failures on the
        workflow run as it isn't properly reported when doing step wise
        execution.
        """
        run_step = asyncio.create_task(handler.run_step())

        cancelling = False
        wait_timeout = 5
        while True:
            done, _pending = await asyncio.wait([run_step], timeout=wait_timeout, return_when=asyncio.ALL_COMPLETED)
            if done:
                return run_step.result() or []
            if handler.cancelled():
                break
            if handler.is_done():
                if not cancelling:
                    logger.warning(f"Workflow run run[{run_id}] was done before it could produce any events. Attempting clean up")
                    cancelling = True
                    run_step.cancel()
                if not run_step.done():
                    logger.warning(f"Workflow run run[{run_id}] was cancelled, but the step is still running. Clean up failed.")
                    break

        raise Exception(
            f"Workflow run run[{run_id}] was cancelled before it could produce any events."
        )

    def ensure_wrapped_response(
        self, handler: WorkflowHandler
    ) -> WrappedResponse:
        """Wrap a response in a WrappedResponse."""
        response = handler.result()
        if not isinstance(response, ResponseType):
            return WrappedResponse(
                handler=handler,
                response=AnyResponse(raw=response),
            )
        return WrappedResponse(handler=handler, response=response)
    
    @step
    def exception_handler(self, event: ExceptionEvent) -> StopEvent:
        """Handle exceptions that occur during the workflow execution."""
        logger.error(f"Exception occurred in workflow: {event.error}")

        return StopEvent(result=ErrorResponse(message=str(event.error)))


class SingleInstrumentedAgentWorkflow(MixableWorkflow):
    registry: ResourceDependency[AgentRegistry]
    agent_name: ResourceDependency[str]

    @step
    async def handle_start(self, context: Context, event: StartEvent) -> StopEvent:
        """Handle the start event of the workflow."""
        logger.info("Workflow started.")
        agent = await self.registry.get_agent(self.agent_name)
        response = await agent.run_safe(event.message)

        return StopEvent(result=response)


def agent_as_chat_workflow(
    config: AgentConfig,
    registry: AgentRegistry,
    agent_name: str,
) -> MixableWorkflow:
    """Create an instrumented agent workflow from an agent name in the registry"""

    resolver = ResourceResolver.from_resources(
        registry=registry,
        config=config,
        agent_name=agent_name,
    )

    return SingleInstrumentedAgentWorkflow(resolver=resolver)
