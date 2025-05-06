import logging
from typing import List, Optional

from llama_index.core.agent.workflow import ReActAgent
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

from .config import AgentConfig, GeminiLLMConfig, GoogleGenAILLMConfig, LocalLLMConfig
from .errors import AgentConfigError, AgentRuntimeError

logger = logging.getLogger("oso-agent")


class Agent:
    """LlamaIndex ReAct agent with configured tools and LLM."""

    def __init__(self, config: AgentConfig):
        """Initialize agent attributes."""
        self.config = config
        self.agent: Optional[ReActAgent] = None

    @classmethod
    async def create(cls, config: AgentConfig):
        """Async factory method to create and initialize an Agent."""
        agent = cls(config)
        agent.agent = await agent._create_agent()
        return agent

    def _setup_telemetry(self) -> Optional[trace_sdk.TracerProvider]:
        """Setup OpenTelemetry tracing if enabled."""
        if not self.config.enable_telemetry:
            return None

        try:
            tracer_provider = trace_sdk.TracerProvider()

            logger.info(
                f"Setting up telemetry with Phoenix at {self.config.arize_phoenix_traces_url}"
            )
            phoenix_exporter = HTTPSpanExporter(
                endpoint=self.config.arize_phoenix_traces_url
            )
            phoenix_processor = SimpleSpanProcessor(phoenix_exporter)
            tracer_provider.add_span_processor(span_processor=phoenix_processor)

            LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("Telemetry successfully initialized")
            return tracer_provider
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}")
            return None

    def _create_local_tools(self) -> List[BaseTool]:
        """Create and return local tools."""

        def multiply(a: float, b: float) -> float:
            """Multiplies two numbers together."""
            logger.debug(f"Multiplying {a} and {b}")
            return a * b

        return [
            FunctionTool.from_defaults(multiply),
        ]

    async def _create_mcp_tools(self) -> List[FunctionTool]:
        """Create and return MCP tools if enabled."""
        if not self.config.use_mcp:
            logger.info("MCP tools disabled, skipping")
            return []

        try:
            logger.info(f"Initializing MCP client with URL: {self.config.oso_mcp_url}")
            mcp_client = BasicMCPClient(self.config.oso_mcp_url)
            mcp_tool_spec = McpToolSpec(
                client=mcp_client,
                allowed_tools=self.config.allowed_mcp_tools,
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
            if self.config.use_mcp:
                raise AgentConfigError(f"Failed to initialize MCP tools: {e}") from e
            return []

    async def _create_agent(self) -> ReActAgent:
        """Create and configure the ReAct agent."""
        logger.info("Setting up telemetry")
        self._setup_telemetry()

        try:
            llm = await self._setup_llm(self.config)

            logger.info("Creating agent tools")
            local_tools = self._create_local_tools()
            mcp_tools = await self._create_mcp_tools()
            tools = local_tools + mcp_tools
            logger.info(f"Created {len(tools)} total tools")

            logger.info("Initializing ReAct agent")
            return ReActAgent(
                tools=tools,
                llm=llm,
                system_prompt=self.config.system_prompt,
            )
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise AgentConfigError(f"Failed to create agent: {e}") from e
        
    async def _setup_llm(self, config: AgentConfig):
        """Setup the LLM for the agent depending on the configuration"""
        match config.llm:
            case LocalLLMConfig(ollama_model=model, ollama_url=base_url, ollama_timeout=timeout):
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
                raise AgentConfigError(
                    f"Unsupported LLM type: {config.llm.type}"
                )
        

    async def run(self, query: str) -> str:
        """Run a query through the agent."""
        try:
            logger.info(f"Running query: {query}")
            if not self.agent:
                raise AgentRuntimeError("Agent not initialized")
            response = await self.agent.run(query)
            return str(response)
        except Exception as e:
            logger.error(f"Error running query: {e}")
            raise AgentRuntimeError(f"Error running query: {e}") from e
