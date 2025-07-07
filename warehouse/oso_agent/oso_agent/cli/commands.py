import asyncio
import json
import logging
import sys
import typing as t

import click
import opentelemetry.trace as trace
import uvicorn
from dotenv import load_dotenv
from llama_index.core.llms import ChatMessage, MessageRole
from oso_agent.tool.storage_context import setup_storage_context
from pyoso import Client

from ..agent import setup_default_agent_registry
from ..eval.experiment_registry import get_experiments
from ..server.bot import setup_bot
from ..server.definition import BotConfig
from ..tool.embedding import create_embedding
from ..tool.llm import create_llm
from ..tool.oso_mcp_client import OsoMcpClient
from ..tool.oso_text2sql import create_oso_query_engine, index_oso_tables
from ..types import ErrorResponse, SemanticResponse, SqlResponse, StrResponse
from ..util.asyncbase import setup_nest_asyncio
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentError, AgentRuntimeError
from ..util.log import setup_logging
from ..util.tracing import setup_telemetry
from .utils import common_options, pass_config

load_dotenv()
setup_nest_asyncio()

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


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
    config = AgentConfig()
    setup_logging(verbose)
    setup_telemetry(config)
    ctx.obj = config


@cli.command()
@click.option(
    "--port",
    "-p",
    default=8888,
    help="Port to run the OSO Agent server on",
)
@click.option(
    "--host",
    "-H",
    default="localhost",
    help="Host to run the OSO Agent server on",
)
def serve(port: int, host: str):
    """Run the OSO Agent server."""
    uvicorn_config = uvicorn.Config("oso_agent.server.server:app", host=host, port=port)
    server = uvicorn.Server(uvicorn_config)
    try:
        logger.info(f"Starting OSO Agent server on {host}:{port}")
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


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
            length=1,
            label=f'Processing query "{query}"',
            show_eta=False,
            show_percent=False,
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

@cli.command()
@pass_config
def initialize_vector_store(config: AgentConfig):
    """Index OSO tables for the agent.

    This command indexes the OSO tables into a vector store to enable efficient
    querying and retrieval of data, this should be done outside of the agent's
    runtime so that the agent doesn't such a long startup time.

    Currently we support either a local vector store or a Google GenAI vector
    store.
    """
    try:
        oso_client = Client(
            api_key=config.oso_api_key.get_secret_value(),
        )
        embed = create_embedding(config)
        storage_context = setup_storage_context(config, embed_model=embed)

        asyncio.run(index_oso_tables(
            config=config,
            storage_context=storage_context,
            oso_client=oso_client,
            embed_model=embed,
        ))

        click.echo("\nOSO tables indexed successfully.")
    except Exception as e:
        click.echo(f"Error indexing OSO tables: {e}", err=True)
        raise e
        sys.exit(1)


async def _run_query(query: str, config: AgentConfig) -> str:
    """Run a query through the agent asynchronously."""

    with tracer.start_as_current_span("cli#run_query", kind=trace.SpanKind.CLIENT):
        registry = await setup_default_agent_registry(config)
        agent = await registry.get_agent(config.agent_name)
        click.echo(
            f"Query started with agent={config.agent_name} and model={config.llm.type}"
        )
        wrapped_response = await agent.run(query)
        match wrapped_response.response:
            case StrResponse(blob=blob):
                return blob
            case SemanticResponse(query=semantic_query):
                return str(semantic_query)
            case SqlResponse(query=sql_query):
                return str(sql_query)
            case ErrorResponse(message=message, details=details):
                raise AgentRuntimeError(
                    f"Error from agent: {message}. Details: {details}"
                )
            case _:
                raise AgentRuntimeError(
                    f"Unexpected response type from agent: {wrapped_response.response.type}"
                )


class JsonType(click.ParamType):
    name = "json"

    def convert(self, value, param, ctx) -> dict[t.Any, t.Any]:
        if not isinstance(value, str):
            return value

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            self.fail(f"{value!r} is not valid JSON", param, ctx)


@cli.command()
@click.argument("experiment_name", required=True)
@click.option(
    "--experiment-options",
    "-o",
    type=JsonType(),
    default="{}",
    help="JSON-encoded options for the experiment",
)
@click.option(
    "--example-ids",
    "-e",
    type=str,
    help="Comma-separated list of example IDs to run (e.g. 12,13,14).",
    default="",
)
@pass_config
def experiment(
    config: AgentConfig, experiment_name: str, experiment_options: dict[str, t.Any], example_ids: str
):
    """Run a single experiment through the agent.

    experiment_name is the name of the experiment to run.
    """
    try:
        with click.progressbar(
            length=1, label="Processing experiment", show_eta=False, show_percent=False
        ) as b:
            experiment_options = {
                **experiment_options,
                "example_ids": [s.strip() for s in example_ids.split(",") if s.strip()]
            }

            response = asyncio.run(
                _run_experiment(experiment_name, config, experiment_options)
            )
            b.update(1)

        click.echo("\nResponse:")
        click.echo("─" * 80)
        click.echo(response)
        click.echo("─" * 80)
    except AgentError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _run_experiment(
    experiment_name: str, config: AgentConfig, experiment_options: dict[str, t.Any]
) -> str:
    """Run an experiment through the agent asynchronously."""
    registry = await setup_default_agent_registry(config)
    click.echo(
        f"Experiment {experiment_name} started with agent={config.agent_name} and model={config.llm.type}"
    )

    experiments = get_experiments()
    if experiment_name in experiments:
        experiment_func = experiments[experiment_name]
        # Run the text2sql experiment
        response = await experiment_func(config, registry, experiment_options)
        click.echo(f"...{experiment_name} experiment completed.")
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
        registry = await setup_default_agent_registry(config)
        agent = await registry.get_agent(config.agent_name)
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
                        history.append(
                            ChatMessage(
                                role=MessageRole.USER,
                                content=query,
                            )
                        )
                        history.append(
                            ChatMessage(
                                role=MessageRole.ASSISTANT,
                                content=response,
                            )
                        )
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
        # Example of using the OsoMcpClient to get table schema
        client = OsoMcpClient(config.oso_mcp_url)
        result = await client.get_table_schema("projects_v1")
        print("Table schema for 'projects_v1':")
        print(result)
        print("─" * 80)
        result = await client.query_oso("SELECT * FROM projects_v1 LIMIT 10")
        print("Sample data from 'projects_v1':")
        print(result)
        print("─" * 80)

        # Example of using the OSO query engine
        llm = create_llm(config)
        embed = create_embedding(config)

        storage_context = setup_storage_context(config, embed_model=embed)

        query_engine = await create_oso_query_engine(
            config,
            storage_context,
            llm,
            embed,
        )
        response = query_engine.query(
            "Get the first 10 projects in 'optimism' collection"
        )
        print("Response from OSO query engine:")
        print(response)
        print("─" * 80)

        # Demo queries with agent
        registry = await setup_default_agent_registry(config)
        agent = await registry.get_agent(config.agent_name)
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


@cli.command()
@pass_config
def discord(config):
    """Run the Discord bot

    experiment_name is the name of the experiment to run.
    """
    bot_config = BotConfig()
    try:
        asyncio.run(_discord_bot_main(bot_config))
    except AgentConfigError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)


async def _discord_bot_main(config: BotConfig) -> None:
    """Testing function to run the bot manually"""
    registry = await setup_default_agent_registry(config)
    bot = await setup_bot(config, registry)
    await bot.login(config.discord_bot_token.get_secret_value())
    task = asyncio.create_task(bot.connect())
    try:
        logger.info("Running bot")
        await asyncio.sleep(10000)
    finally:
        logger.info("Closing bot")
        await bot.close()
        await task
