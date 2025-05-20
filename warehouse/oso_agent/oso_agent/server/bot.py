import asyncio

from discord import Client, Intents, Message, TextChannel
from oso_agent.agent.agent import Agent
from oso_agent.server.definition import BotConfig


def setup_bot(config: BotConfig, agent: Agent):
    intents = Intents.default()
    intents.message_content = True

    client = Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")

    @client.event
    async def on_message(message: Message):
        print(message)
        if message.author == client.user:
            return

        channel = message.channel
        if not isinstance(channel, TextChannel):
            return
        
        if str(channel.id) != config.discord_channel_id.get_secret_value():
            return

        if message.content.startswith("!run_eval"):
            await message.channel.send("Running eval!")

    return client

async def bot_main():
    """Testing function to run the bot manually"""
    import dotenv
    dotenv.load_dotenv()

    config = BotConfig()
    bot = setup_bot(config, None) # type: ignore
    await bot.login(config.discord_bot_token.get_secret_value())
    task = asyncio.create_task(bot.connect())
    try:
        print("Running bot")
        await asyncio.sleep(10000)
    finally:
        print("Closing bot")
        await bot.close()
        await task


if __name__ == "__main__":
    # Hack: should move this to the cli module
    asyncio.run(bot_main())
