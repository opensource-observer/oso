import asyncio

from dotenv import load_dotenv
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama

#from oso_mcp import mcp

load_dotenv()
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434"
OSO_MCP_URL = "http://localhost:8000/sse"

# Define a simple calculator tool
def multiply(a: float, b: float) -> float:
    """Useful for multiplying two numbers."""
    return a * b

local_tools = [
    FunctionTool.from_defaults(multiply),
]

# MCP
#mcp_client = BasicMCPClient(OSO_MCP_URL)
#mcp_tool_spec = McpToolSpec(
#    client=mcp_client,
    # Optional: Filter the tools by name
    # allowed_tools=["tool1", "tool2"],
#)
#mcp_tools = mcp_tool_spec.to_tool_list()

# Create an agent workflow with our calculator tool
llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_URL, request_timeout=60.0)
tools = local_tools #+ mcp_tools
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

# Run the agent
if __name__ == "__main__":
    asyncio.run(
        main(),
        #mcp.run(transport="stdio")
    )