import logging
import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from phoenix.otel import register

from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentMissingError
from .react_agent import create_react_agent
from .sql_agent import create_sql_agent

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
AgentDict = t.Dict[str, BaseWorkflowAgent]

def _setup_telemetry(config: AgentConfig) -> t.Optional[trace_sdk.TracerProvider]:
    """Setup OpenTelemetry tracing if enabled."""
    if not config.enable_telemetry:
        return None

    try:
        if config.arize_phoenix_use_cloud:
            if not config.arize_phoenix_api_key.get_secret_value():
                logger.warning(
                    "Arize Phoenix API key is empty but cloud mode is enabled"
                )
                return None

            logger.info("Setting up telemetry with Arize Phoenix Cloud")

            tracer_provider = register(
                project_name="oso-agent",
                endpoint="https://app.phoenix.arize.com/v1/traces",
                batch=True,
                headers={
                    "api_key": config.arize_phoenix_api_key.get_secret_value(),
                },
                set_global_tracer_provider=False,
                verbose=False,
            )

            LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("Phoenix Cloud telemetry successfully initialized")
            return tracer_provider

        logger.info(
            f"Setting up telemetry with local Phoenix at {config.arize_phoenix_traces_url}"
        )
        tracer_provider = trace_sdk.TracerProvider()
        phoenix_exporter = HTTPSpanExporter(endpoint=config.arize_phoenix_traces_url)
        phoenix_processor = SimpleSpanProcessor(phoenix_exporter)
        tracer_provider.add_span_processor(span_processor=phoenix_processor)

        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("Local telemetry successfully initialized")
        return tracer_provider

    except Exception as e:
        logger.error(f"Failed to initialize telemetry: {e}")
        return None


async def _create_agents(config: AgentConfig) -> AgentDict:
    """Create and configure the ReAct agent."""
    registry: AgentDict = {}

    try:
        logger.info("Creating all agents...")
        registry["react"] = await create_react_agent(config)
        registry["sql"] = await create_sql_agent(config)
        return registry
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise AgentConfigError(f"Failed to create agent: {e}") from e

class AgentRegistry:
    """Registry of all agents."""
    def __init__(
        self,
        config: AgentConfig,
        agents: AgentDict = {},
    ):
        """Initialize registry."""
        self.config = config
        self.agents  = agents

    @classmethod
    async def create(cls, config: AgentConfig):
        logger.info("Initializing the OSO agent registry...")
        _setup_telemetry(config)
        agents = await _create_agents(config)
        registry = cls(config, agents)
        logger.info("... agent registry ready")
        return registry

    def get_agent(self, name: str) -> BaseWorkflowAgent:
        agent = self.agents.get(name)
        if agent is None:
            raise AgentMissingError(f"Agent '{name}' not found in the registry.")
        return self.agents[name]