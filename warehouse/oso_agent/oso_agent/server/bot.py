import logging
from typing import Optional

from discord import Intents, Member
from discord.ext.commands import Bot

from ..agent.agent_registry import AgentRegistry
from ..eval.experiment_registry import get_experiments
from ..types.response import WrappedResponse
from .definition import BotConfig

logger = logging.getLogger(__name__)

COMMAND_PREFIX = "!"

def response_to_str(response: WrappedResponse) -> str:
    """Convert a WrappedResponse to a string representation."""
    if response.response.type == "str":
        return response.response.blob
    elif response.response.type == "semantic":
        return f"Semantic Query: {response.response.query}"
    elif response.response.type == "sql":
        return f"SQL Query: {response.response.query.query}"
    elif response.response.type == "error":
        return f"Error: {response.response.message} - {response.response.details}"
    else:
        return "Unknown response type"

async def setup_bot(config: BotConfig, registry: AgentRegistry):
    intents = Intents.default()
    intents.message_content = True
    default_agent = await registry.get_agent(config.agent_name)

    bot = Bot(command_prefix=COMMAND_PREFIX,intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user}")

    @bot.command()
    async def hello(ctx, *, member: Optional[Member] = None):
        """Says hello"""
        logger.info(f"Hello command invoked by {ctx.author.name} in {ctx.channel.name}")
        member = member or ctx.author
        await ctx.send(f'Hello {member.name}~')

    @bot.command()
    async def ask(ctx, agent_name: str, *, query: str):
        """Ask a specific agent a query"""
        logger.info(f"Ask command to {agent_name} invoked by {ctx.author.name} in {ctx.channel.name}")
        logger.info(query)
        try:
            agent = await registry.get_agent(agent_name)
            response = await agent.run_safe(query)
            await ctx.send(response_to_str(response))
        except Exception as e:
            logger.error(f"Error asking agent {agent_name}: {e}")
            await ctx.send(f"Error asking gent {agent_name}. {e}")
            return

    @bot.command()
    async def query(ctx, *, query: str):
        """Use the default agent"""
        logger.info(f"Query command invoked by {ctx.author.name} in {ctx.channel.name}")
        logger.info(query)
        response = await default_agent.run_safe(query)
        await ctx.send(response_to_str(response))

    @bot.command()
    async def noice(ctx):
        """noice"""
        await ctx.send("https://tenor.com/view/nice-nooice-bling-key-and-peele-gif-4294979")

    @bot.command()
    async def run_eval(ctx, experiment_name: str, agent_name: Optional[str] = config.agent_name):
        logger.info(
            f"Experiment {experiment_name} started with agent={agent_name} and model={config.llm.type}"
        )

        await ctx.send("Running the experiment now! This might take a while...")

        try:
            agent = await registry.get_agent(agent_name) if agent_name else default_agent
            logger.debug("loading experiment registry")
            experiments = get_experiments()
            if experiment_name in experiments:
                logger.debug(f"Running experiment: {experiment_name} with agent: {agent_name}")
                # Run the experiment
                experiment_func = experiments[experiment_name]
                updated_config = config.model_copy(update={"agent_name": agent_name})
                response = await experiment_func(updated_config, agent)
                logger.info(f"...{experiment_name} experiment completed.")
                await ctx.send(str(response))
            else:
                await ctx.send(f"Experiment {experiment_name} not found. Please check the experiment name.")
        except Exception as e:
            logger.error(f"Error running {experiment_name} with agent {agent_name}: {e}")
            await ctx.send(f"Error running {experiment_name} with agent {agent_name}: {e}")
        

    return bot