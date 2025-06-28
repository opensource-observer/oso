import inspect
import logging
import typing as t

from oso_agent.types.response import WrappedResponse

from ..resources import ResolverFactory
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentMissingError
from .base import MixableWorkflow, ResourceResolver

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
WorkflowDict = t.Dict[str, MixableWorkflow]

WorkflowFactory = t.Callable[[AgentConfig, ResourceResolver], t.Awaitable[MixableWorkflow]]
ResponseWrapper = t.Callable[[t.Any], WrappedResponse]

def default_workflow_factory(
    cls: t.Type[MixableWorkflow],
):
    """Default workflow factory that raises an error if no specific factory is provided."""
    async def _factory(
        config: AgentConfig, resolver: ResourceResolver
    ) -> MixableWorkflow:
        return cls(resolver, timeout=config.workflow_timeout)
    return _factory

class WorkflowRegistry:
    """Registry of all workflows."""
    def __init__(
        self,
        config: AgentConfig,
        resolver_factory: ResolverFactory,
    ):
        """Initialize registry."""
        self.config = config
        self.workflow_factories: dict[str, WorkflowFactory] = {}
        self.workflows: WorkflowDict = {}
        self.resolver_factory = resolver_factory

    def add_workflow(self, name: str, workflow: WorkflowFactory | t.Type[MixableWorkflow]):
        """Add a workflow to the registry."""
        if name in self.workflow_factories:
            raise AgentConfigError(f"Workflow '{name}' already exists in the registry.")
        if inspect.isclass(workflow):
            if not issubclass(workflow, MixableWorkflow):
                raise AgentConfigError(f"Workflow '{name}' must be a subclass of MixableWorkflow.")
            factory = default_workflow_factory(workflow)
        elif inspect.isfunction(workflow):
            factory = workflow
        else:
            raise AgentConfigError(f"Workflow '{name}' must be a callable or a class.")
        self.workflow_factories[name] = factory
        logger.info(f"Workflow factory '{name}' added to the registry.")

    async def get_workflow(self, name: str) -> MixableWorkflow:
        workflow = self.workflows.get(name)
        if workflow is None and name not in self.workflow_factories:
            raise AgentMissingError(f"Workflow '{name}' not found in the registry.")
        if workflow is None:
            factory = self.workflow_factories[name]
            resolver = await self.resolver_factory(self.config)
            workflow = await factory(self.config, resolver)
            self.workflows[name] = workflow
            logger.info(f"Workflow '{name}' lazily created and added to the registry.")
        return self.workflows[name]