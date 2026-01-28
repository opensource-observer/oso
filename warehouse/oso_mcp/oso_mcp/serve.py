"""
This should be considered a _test_ only module that is used to run the dev
server for FastMCP
"""

from dotenv import load_dotenv
from oso_core.logging import setup_module_logging
from oso_mcp.server.app import setup_mcp_app
from oso_mcp.server.config import MCPConfig

load_dotenv()

setup_module_logging("oso_mcp")

config = MCPConfig()

app = setup_mcp_app(config)
