import asyncio
import os

from dotenv import load_dotenv
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

load_dotenv()

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OSO_MCP_URL = os.environ.get("OSO_MCP_URL", "http://localhost:8000/sse")
ARIZE_PHOENIX_TRACES_URL = os.environ.get("ARIZE_PHOENIX_TRACES_URL", "http://localhost:6006/v1/traces")

# Add Phoenix
span_phoenix_processor = SimpleSpanProcessor(
    HTTPSpanExporter(endpoint=ARIZE_PHOENIX_TRACES_URL),
)

# Add them to the tracer
tracer_provider = trace_sdk.TracerProvider()
tracer_provider.add_span_processor(span_processor=span_phoenix_processor)

# Instrument the application
LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

# Define a simple calculator tool
def multiply(a: float, b: float) -> float:
    """Useful for multiplying two numbers."""
    return a * b

local_tools = [
    FunctionTool.from_defaults(multiply),
]

# MCP
mcp_client = BasicMCPClient(OSO_MCP_URL)
mcp_tool_spec = McpToolSpec(
    client=mcp_client,
    # Optional: Filter the tools by name
    # allowed_tools=["tool1", "tool2"],
)
mcp_tools = mcp_tool_spec.to_tool_list()

# Create an agent workflow with our calculator tool
llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_URL, request_timeout=60.0)
tools = local_tools + mcp_tools
#agent = FunctionAgent(
#    tools=[multiply],
agent = ReActAgent(
    tools=tools,
    llm=llm,
    system_prompt="You are a helpful assistant that can multiply two numbers.",
)

async def main():
    # Run the agent
    response = await agent.run("What is 1234 * 4567?")
    print(str(response))
    response = await agent.run("Please give me the first 10 rows of the table `projects_v1`")
    print(str(response))

# Run the agent
if __name__ == "__main__":
    asyncio.run(main())
