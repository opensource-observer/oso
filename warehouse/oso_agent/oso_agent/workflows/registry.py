import inspect
import logging
import typing as t

from oso_agent.types.response import WrappedResponse

from ..resources import ResolverFactory
from ..util.config import AgentConfig, WorkflowConfig
from ..util.errors import AgentConfigError, AgentMissingError
from .base import MixableWorkflow, ResourceResolver, StartingWorkflow

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
WorkflowDict = t.Dict[str, StartingWorkflow[t.Any]]

WorkflowFactory = t.Callable[
    [AgentConfig, ResourceResolver], t.Awaitable[StartingWorkflow[t.Any]]
]
ResponseWrapper = t.Callable[[t.Any], WrappedResponse]


def default_workflow_factory(
    cls: t.Type[StartingWorkflow[t.Any]],
):
    """Default workflow factory that raises an error if no specific factory is provided."""

    async def _factory(
        config: AgentConfig, resolver: ResourceResolver
    ) -> StartingWorkflow[t.Any]:
        return cls(resolver, timeout=config.workflow_timeout)

    return _factory


T = t.TypeVar("T", bound=MixableWorkflow)


class WorkflowRegistry:
    """Registry of all workflows."""

    def __init__(
        self,
        config: AgentConfig,
        default_resolver: ResourceResolver,
        workflow_resolver_factory: ResolverFactory,
    ):
        """Initialize registry."""
        self.config = config
        self.workflow_factories: dict[str, WorkflowFactory] = {}
        self.default_resolver = default_resolver
        self.workflow_resolver_factory = workflow_resolver_factory

    def add_workflow(
        self, name: str, workflow: WorkflowFactory | t.Type[StartingWorkflow]
    ):
        """Add a workflow to the registry."""
        if name in self.workflow_factories:
            raise AgentConfigError(f"Workflow '{name}' already exists in the registry.")
        if inspect.isclass(workflow):
            if not issubclass(workflow, StartingWorkflow):
                raise AgentConfigError(
                    f"Workflow '{name}' must be a subclass of MixableWorkflow."
                )
            factory = default_workflow_factory(workflow)
        elif inspect.isfunction(workflow):
            factory = workflow
        else:
            raise AgentConfigError(f"Workflow '{name}' must be a callable or a class.")
        self.workflow_factories[name] = factory
        logger.info(f"Workflow factory '{name}' added to the registry.")

    def add_alias(self, alias: str, original: str):
        """Add an alias for an existing workflow."""
        if alias in self.workflow_factories:
            raise AgentConfigError(
                f"Workflow '{alias}' already exists in the registry."
            )
        if original not in self.workflow_factories:
            raise AgentConfigError(
                f"Original workflow '{original}' does not exist in the registry."
            )
        self.workflow_factories[alias] = self.workflow_factories[original]
        logger.info(f"Workflow alias '{alias}' added for '{original}'.")

    async def get_workflow(
        self,
        name: str,
        workflow_config: WorkflowConfig,
    ) -> StartingWorkflow[t.Any]:
        """Get a workflow instance of specific type."""
        if name not in self.workflow_factories:
            raise AgentMissingError(f"Workflow '{name}' not found in the registry.")

        factory = self.workflow_factories[name]
        resolver = await self.workflow_resolver_factory(
            self.default_resolver, self.config, workflow_config
        )

        workflow = await factory(
            self.config, resolver.merge_resolver(self.default_resolver)
        )
        logger.debug(f"Created workflow '{name}' of type {type(workflow).__name__}")

        return workflow
