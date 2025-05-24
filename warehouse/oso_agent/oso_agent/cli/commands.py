import asyncio
import logging
import sys

import click
from dotenv import load_dotenv
from llama_index.core.llms import ChatMessage, MessageRole

from ..agent.registry import AgentRegistry
from ..eval.text2sql import text2sql_experiment
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentError, AgentRuntimeError
from ..util.log import setup_logging
from .utils import common_options, pass_config

load_dotenv()

logger = logging.getLogger("oso-agent")

async def create_agent(config: AgentConfig):
    registry = await AgentRegistry.create(config)
    agent = registry.get_agent(config.agent_name)
    return agent

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
    OSO agents. The agent can use both local tools and MCP tools.
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
def query(config, query, agent_name, ollama_model, ollama_url):
    """Run a single query through the agent.

    QUERY is the text to send to the agent.
    """
    updated_config = config.update(
        agent_name=agent_name, ollama_model=ollama_model, ollama_url=ollama_url
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
    agent = await create_agent(config)
    click.echo(
        f"Query started with agent={config.agent_name} and model={config.llm.type}"
    )
    return await agent.run(query)

@cli.command()
@click.argument("experiment_name", required=True)
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
def experiment(config, experiment_name, agent_name, ollama_model, ollama_url):
    """Run a single experiment through the agent.

    experiment_name is the name of the experiment to run.
    """
    updated_config = config.update(
        agent_name=agent_name, ollama_model=ollama_model, ollama_url=ollama_url
    )

    try:
        with click.progressbar(
            length=1, label="Processing experiment", show_eta=False, show_percent=False
        ) as b:
            response = asyncio.run(_run_experiment(experiment_name, updated_config))
            b.update(1)

        click.echo("\nResponse:")
        click.echo("─" * 80)
        click.echo(response)
        click.echo("─" * 80)
    except AgentError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _run_experiment(experiment_name: str, config: AgentConfig) -> str:
    """Run an experiment through the agent asynchronously."""
    agent = await create_agent(config)
    click.echo(
        f"Experiment {experiment_name} started with agent={config.agent_name} and model={config.llm.type}"
    )

    if experiment_name == "text2sql":
        # Run the text2sql experiment
        response = await text2sql_experiment(config, agent)
        click.echo("...text2sql experiment completed.")
        return str(response)
    else:
        raise AgentRuntimeError(
            f"Experiment {experiment_name} not found. Please check the experiment name."
        )

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
def shell(config, agent_name, ollama_model, ollama_url):
    """Start an interactive shell session with the agent.

    This command starts a REPL-like interface where you can
    type queries and get responses from the agent.
    """
    updated_config = config.update(
        agent_name=agent_name, ollama_model=ollama_model, ollama_url=ollama_url
    )

    try:
        asyncio.run(_run_interactive_session(updated_config))
    except AgentConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


async def _run_interactive_session(config: AgentConfig):
    """Run an interactive session with the agent asynchronously."""
    try:
        agent = await create_agent(config)
        click.echo(
            f"Interactive agent session started with agent={config.agent_name} and model={config.llm.type}"
        )
        click.echo("Type 'exit' or press Ctrl+D to quit.")

        history: list[ChatMessage] = []

        while True:
            try:
                query = click.prompt("\nQuery", type=str)
                if query.lower() in ("exit", "quit"):
                    break

                try:
                    with click.progressbar(
                        length=1, label="Thinking", show_eta=False, show_percent=False
                    ) as b:
                        response = await agent.run(query, chat_history=history)
                        history.append(ChatMessage(
                            role=MessageRole.USER, content=query,
                        ))
                        history.append(ChatMessage(
                            role=MessageRole.ASSISTANT, content=response,
                        ))
                        print(history)
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
    help="Ollama model to use",
)
@click.option(
    "--ollama-url",
    "-u",
    help="URL for the Ollama API",
)
@pass_config
def demo(config, agent_name, ollama_model, ollama_url):
    """Run demo queries to showcase agent capabilities.

    This command runs a set of predefined queries to demonstrate
    the agent's functionality with local and MCP tools.
    """
    updated_config = config.update(
        agent_name=agent_name,
        ollama_model=ollama_model,
        ollama_url=ollama_url,
    )

    try:
        asyncio.run(_run_demo(updated_config))
    except AgentConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


async def _run_demo(config: AgentConfig):
    """Run demo queries asynchronously."""
    try:
        agent = await create_agent(config)
        click.echo(
            f"Demo started with agent={config.agent_name} and model={config.llm.type}"
        )
        queries = [
            "What is 1234 * 4567?",
            "Please give me the first 10 rows of the table `projects_v1`",
        ]

        click.echo(f"Running demo with model: {config.llm.type}")

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
