import logging
import typing as t

from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.core.workflow.workflow import WorkflowMeta
from opentelemetry import trace
from oso_agent.agent.agent_registry import AgentRegistry
from oso_agent.types.response import ResponseType
from oso_agent.util.config import AgentConfig

from ..types import ErrorResponse, WrappedResponse

ResponseWrapper = t.Callable[[t.Any], WrappedResponse]

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


V = t.TypeVar("V")

class ResolverEnabled(t.Protocol):
    resolver: "ResourceResolver"


class ResourceDependency(t.Generic[V]):
    def __set_name__(self, _owner, name):
        self._name = name

    def __get__(self, obj: ResolverEnabled, owner: t.Any) -> V:
        return obj.resolver.get_resource(self._name)

    def __set__(self, obj: t.Optional[object], value: V) -> None:
        raise AttributeError(
            f"Cannot set resource '{self._name}'. Resources are immutable after initialization."
        )


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
    
    def validate_for_required_resources(self, resources_dict: dict[str, type]) -> t.List[str]:
        """Check if all resources in the dictionary are available in the resolver."""
        missing_resources = []
        for name, resource_type in resources_dict.items():
            if name not in self._resources:
                missing_resources.append(f"Resource '{name}' is missing from the resolver.")
            elif not isinstance(self._resources[name], resource_type):
                missing_resources.append(
                    f"Resource '{name}' is of type {type(self._resources[name])}, "
                    f"but should be {resource_type}."
                )
        return missing_resources


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
                        dct[attr_name] = ResourceDependency()
    
        for attr_name, attr_type in dct.get('__annotations__', {}).items():
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
                    dct[attr_name] = ResourceDependency()

        cls._required_resources = required_resources
        return super().__new__(cls, name, bases, dct)


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

        # Usually we shouldn't do much error handling in the constructor but the
        # metaclass necessitates that we validate the required resources
        # available at this point.

        missing_resources = resolver.validate_for_required_resources(self.__class__._required_resources)
        if missing_resources:
            raise TypeError(
                f"Missing required resources for {self.__class__.__name__}: "
                + ", ".join(missing_resources)
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
        agent_name=agent_name,
    )

    return SingleInstrumentedAgentWorkflow(resolver=resolver)
