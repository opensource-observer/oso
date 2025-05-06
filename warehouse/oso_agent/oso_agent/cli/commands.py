import asyncio
import logging
import sys

import click

from ..agent.agent import Agent
from ..agent.config import AgentConfig
from ..agent.errors import AgentConfigError, AgentError, AgentRuntimeError
from ..utils.log import setup_logging
from .utils import common_options, pass_config

logger = logging.getLogger("oso-agent")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (can be used multiple times)",
)
@click.pass_context
def cli(ctx, verbose):
    """OSO Agent CLI with ReAct capabilities.

    This tool provides a command-line interface for interacting with a
    ReAct agent. The agent can use both local tools and MCP tools.
    """
    setup_logging(verbose)

    ctx.obj = AgentConfig()


@cli.command()
@click.argument("query", required=True)
@common_options
@click.option(
    "--ollama-model",
    "-m",
    help="Ollama model to use",
)
@click.option(
    "--ollama-url",
    "-u",
    help="URL for the Ollama API",
)
@pass_config
def query(config, query, system_prompt, ollama_model, ollama_url):
    """Run a single query through the agent.

    QUERY is the text to send to the agent.
    """
    updated_config = config.update(
        system_prompt=system_prompt, ollama_model=ollama_model, ollama_url=ollama_url
    )

    try:
        with click.progressbar(
            length=1, label="Processing query", show_eta=False, show_percent=False
        ) as b:
            response = asyncio.run(_run_query(query, updated_config))
            b.update(1)

        click.echo("\nResponse:")
        click.echo("─" * 80)
        click.echo(response)
        click.echo("─" * 80)
    except AgentError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _run_query(query: str, config: AgentConfig) -> str:
    """Run a query through the agent asynchronously."""
    agent = await Agent.create(config)
    return await agent.run(query)


@cli.command()
@common_options
@click.option(
    "--ollama-model",
    "-m",
    help="Ollama model to use",
)
@click.option(
    "--ollama-url",
    "-u",
    help="URL for the Ollama API",
)
@pass_config
def shell(config, system_prompt, ollama_model, ollama_url):
    """Start an interactive shell session with the agent.

    This command starts a REPL-like interface where you can
    type queries and get responses from the agent.
    """
    updated_config = config.update(
        system_prompt=system_prompt, ollama_model=ollama_model, ollama_url=ollama_url
    )

    try:
        asyncio.run(_run_interactive_session(updated_config))
    except AgentConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


async def _run_interactive_session(config: AgentConfig):
    """Run an interactive session with the agent asynchronously."""
    try:
        agent = await Agent.create(config)
        click.echo(
            f"Interactive agent session started with model: {config.llm.type}"
        )
        click.echo(f"System prompt: {config.system_prompt}")
        click.echo("Type 'exit' or press Ctrl+D to quit.")

        while True:
            try:
                query = click.prompt("\nQuery", type=str)
                if query.lower() in ("exit", "quit"):
                    break

                try:
                    with click.progressbar(
                        length=1, label="Thinking", show_eta=False, show_percent=False
                    ) as b:
                        response = await agent.run(query)
                        b.update(1)

                    click.echo("\nResponse:")
                    click.echo("─" * 80)
                    click.echo(response)
                    click.echo("─" * 80)
                except AgentRuntimeError as e:
                    click.echo(f"Error: {e}", err=True)
            except (KeyboardInterrupt, EOFError):
                click.echo("\nExiting...")
                break
    except Exception as e:
        click.echo(f"Error in interactive session: {e}", err=True)


@cli.command()
@common_options
@click.option(
    "--ollama-model",
    "-m",
    help="Ollama model to use (defaults to a smaller model for demo)",
    default="llama3.2:3b",
)
@pass_config
def demo(config, system_prompt, ollama_model):
    """Run demo queries to showcase agent capabilities.

    This command runs a set of predefined queries to demonstrate
    the agent's functionality with local and MCP tools.
    """
    demo_system_prompt = (
        system_prompt
        or "You are a helpful assistant that can query the OpenSource Observer datalake."
    )
    updated_config = config.update(
        system_prompt=demo_system_prompt,
        ollama_model=ollama_model,
    )

    try:
        asyncio.run(_run_demo(updated_config))
    except AgentConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


async def _run_demo(config: AgentConfig):
    """Run demo queries asynchronously."""
    try:
        agent = await Agent.create(config)

        queries = [
            "What is 1234 * 4567?",
            "Please give me the first 10 rows of the table `projects_v1`",
        ]

        click.echo(f"Running demo with model: {config.llm.type}")
        click.echo(f"System prompt: {config.system_prompt}")

        for i, query in enumerate(queries, 1):
            click.echo(f"\nDemo query {i}: {query}")
            try:
                with click.progressbar(
                    length=1, label="Processing", show_eta=False, show_percent=False
                ) as b:
                    response = await agent.run(query)
                    b.update(1)

                click.echo("\nResponse:")
                click.echo("─" * 80)
                click.echo(response)
                click.echo("─" * 80)
            except AgentRuntimeError as e:
                click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"Error in demo: {e}", err=True)
