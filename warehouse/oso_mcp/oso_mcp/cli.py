import logging

import click
from dotenv import load_dotenv

from .server.app import setup_mcp_app
from .server.config import MCPConfig
from .utils.log import setup_logging

load_dotenv()
logger = logging.getLogger("oso-mcp")

pass_config = click.make_pass_decorator(MCPConfig, ensure=True)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (can be used multiple times)",
)
@click.pass_context
def cli(ctx, verbose):
    setup_logging(verbose)

    ctx.obj = MCPConfig()


@cli.command()
@pass_config
def serve(config: MCPConfig):
    """Start the OSO MCP server."""
    logger.info("Starting OSO MCP server...")

    mcp_app = setup_mcp_app(config)

    mcp_app.run(transport=config.transport)


@cli.command()
def env_schema():
    """Show the environment variable schema for the MCP server."""
    MCPConfig.print_env_schema()
