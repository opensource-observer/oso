import logging
import typing as t

from oso_agent.agent.agent_registry import AgentRegistry
from oso_agent.types.response import WrappedResponse
from oso_agent.workflows.base import MixableWorkflow

from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentMissingError

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
WorkflowDict = t.Dict[str, MixableWorkflow]

WorkflowFactory = t.Callable[[AgentConfig, AgentRegistry], t.Awaitable[MixableWorkflow]]
ResponseWrapper = t.Callable[[t.Any], WrappedResponse]



class WorkflowRegistry:
    """Registry of all workflows."""
    def __init__(
        self,
        config: AgentConfig,
        agent_registry: AgentRegistry,
    ):
        """Initialize registry."""
        self.config = config
        self.workflow_factories: dict[str, WorkflowFactory] = {}
        self.workflows: WorkflowDict = {}
        self.agent_registry = agent_registry

    def add_workflow(self, name: str, factory: WorkflowFactory):
        """Add a workflow to the registry."""
        if name in self.workflow_factories:
            raise AgentConfigError(f"Workflow '{name}' already exists in the registry.")
        self.workflow_factories[name] = factory
        logger.info(f"Workflow factory '{name}' added to the registry.")

    async def get_workflow(self, name: str) -> MixableWorkflow:
        workflow = self.workflows.get(name)
        if workflow is None and name not in self.workflow_factories:
            raise AgentMissingError(f"Workflow '{name}' not found in the registry.")
        if workflow is None:
            factory = self.workflow_factories[name]
            workflow = await factory(self.config, self.agent_registry)
            self.workflows[name] = workflow
            logger.info(f"Workflow '{name}' lazily created and added to the registry.")
        return self.workflows[name]

    async def eager_load_all_workflows(self):
        """Eagerly load all workflows in the registry."""
        logger.info("Eagerly loading all workflows in the registry...")
        for name in self.workflow_factories.keys():
            await self.get_workflow(name)
        logger.info("All workflows have been eagerly loaded.")