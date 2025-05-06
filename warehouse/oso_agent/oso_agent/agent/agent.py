import logging
import typing as t

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.llms.gemini import Gemini
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from phoenix.otel import register

from .config import AgentConfig, GeminiLLMConfig, GoogleGenAILLMConfig, LocalLLMConfig
from .errors import AgentConfigError

logger = logging.getLogger(__name__)


async def _create_mcp_tools(config: AgentConfig) -> list[FunctionTool]:
    """Create and return MCP tools if enabled."""
    if not config.use_mcp:
        logger.info("MCP tools disabled, skipping")
        return []

    try:
        logger.info(f"Initializing MCP client with URL: {config.oso_mcp_url}")
        mcp_client = BasicMCPClient(config.oso_mcp_url)
        mcp_tool_spec = McpToolSpec(
            client=mcp_client,
            allowed_tools=config.allowed_mcp_tools,
        )
        tools = await mcp_tool_spec.to_tool_list_async()
        tool_names = ", ".join(
            [
                str(tool._metadata.name)
                for tool in tools
                if tool._metadata.name is not None
            ]
        )
        logger.info(f"Loaded {len(tools)} MCP tools: {tool_names}")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize MCP tools: {e}")
        if config.use_mcp:
            raise AgentConfigError(f"Failed to initialize MCP tools: {e}") from e
        return []


async def _setup_llm(config: AgentConfig):
    """Setup the LLM for the agent depending on the configuration"""
    match config.llm:
        case LocalLLMConfig(
            ollama_model=model, ollama_url=base_url, ollama_timeout=timeout
        ):
            logger.info(f"Initializing Ollama LLM with model {config.llm.ollama_model}")
            return Ollama(
                model=model,
                base_url=base_url,
                request_timeout=timeout,
            )
        case GeminiLLMConfig(api_key=api_key, model=model):
            logger.info("Initializing Gemini LLM")
            # Placeholder for Gemini LLM initialization
            return Gemini(api_key=api_key, model=model)
        case GoogleGenAILLMConfig(api_key=api_key, model=model):
            logger.info("Initializing Google GenAI LLM")
            return GoogleGenAI(api_key=api_key, model=model)
        case _:
            raise AgentConfigError(f"Unsupported LLM type: {config.llm.type}")


def _create_local_tools() -> list[BaseTool]:
    """Create and return local tools."""

    def multiply(a: float, b: float) -> float:
        """Multiplies two numbers together."""
        logger.debug(f"Multiplying {a} and {b}")
        return a * b

    return [
        FunctionTool.from_defaults(multiply),
    ]


async def _create_agent(config: AgentConfig) -> ReActAgent:
    """Create and configure the ReAct agent."""
    logger.info("Setting up telemetry")
    _setup_telemetry(config)

    try:
        llm = await _setup_llm(config)

        logger.info("Creating agent tools")
        # local_tools = _create_local_tools()
        mcp_tools = await _create_mcp_tools(config)
        tools = mcp_tools
        logger.info(f"Created {len(tools)} total tools")

        logger.info("Initializing ReAct agent")
        return ReActAgent(
            tools=tools,
            llm=llm,
            system_prompt=config.system_prompt,
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise AgentConfigError(f"Failed to create agent: {e}") from e


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


class Agent:
    """LlamaIndex ReAct agent with configured tools and LLM."""

    def __init__(
        self,
        config: AgentConfig,
        react_agent: ReActAgent,
        tools: list[BaseTool],
        mcp_tools: list[FunctionTool],
    ):
        """Initialize agent attributes."""
        self.config = config
        self.react_agent: ReActAgent = react_agent
        self.tools: list[BaseTool] = tools
        self.mcp_tools: list[FunctionTool] = mcp_tools

    @classmethod
    async def create(cls, config: AgentConfig):
        """Async factory method to create and initialize an Agent."""
        logger.info("Creating agent")
        tools = _create_local_tools()
        mcp_tools = await _create_mcp_tools(config)
        react_agent = await _create_agent(config)

        agent = cls(config, react_agent, tools, mcp_tools)
        return agent

    async def run(
        self, query: str, chat_history: list[ChatMessage] | None = None
    ) -> str:
        """Run a query through the agent."""

        chat_buffer = ChatMemoryBuffer(token_limit=1000000)

        logger.info(f"Running query: {query}")
        chat_history = chat_history or []

        response = await self.react_agent.run(
            query, chat_history=chat_history, memory=chat_buffer
        )
        return str(response)
