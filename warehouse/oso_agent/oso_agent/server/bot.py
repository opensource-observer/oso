import logging
from typing import Optional

from discord import Intents, Member
from discord.ext.commands import Bot
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from ..eval.experiment_registry import get_experiments
from .definition import BotConfig

logger = logging.getLogger(__name__)

COMMAND_PREFIX = "!"

async def setup_bot(config: BotConfig, agent: BaseWorkflowAgent):
    intents = Intents.default()
    intents.message_content = True

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
    async def run_eval(ctx, *, experiment_name: str):
        logger.info(
            f"Experiment {experiment_name} started with agent={config.agent_name} and model={config.llm.type}"
        )

        experiments = get_experiments()
        if experiment_name in experiments:
            # Run the experiment
            experiment_func = experiments[experiment_name]
            response = await experiment_func(config, agent)
            logger.info(f"...{experiment_name} experiment completed.")
            await ctx.send(str(response))
        else:
            await ctx.send(f"Experiment {experiment_name} not found. Please check the experiment name.")

    return bot