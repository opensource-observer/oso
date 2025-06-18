import asyncio
import json
import logging
import typing as t
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.datastructures import State
from fastapi.responses import PlainTextResponse
from oso_agent.agent import setup_default_agent_registry
from oso_agent.server.bot import setup_bot
from oso_agent.server.definition import (
    AgentServerConfig,
    AppLifespanFactory,
    BotConfig,
    ChatRequest,
)
from oso_agent.types.response import AnyResponse
from oso_agent.util.log import setup_logging

from ..types import (
    ErrorResponse,
    SemanticResponse,
    SqlResponse,
    StrResponse,
    WrappedResponse,
    WrappedResponseAgent,
)
from ..util.asyncbase import setup_nest_asyncio
from ..util.tracing import setup_telemetry

setup_nest_asyncio()

load_dotenv()
logger = logging.getLogger(__name__)


def default_lifecycle(config: AgentServerConfig):
    @asynccontextmanager
    async def initialize_app(app: FastAPI):
        setup_telemetry(config)
        registry = await setup_default_agent_registry(config)
        agent = await registry.get_agent(config.agent_name)

        bot_config = BotConfig()
        bot = await setup_bot(bot_config, registry)
        await bot.login(bot_config.discord_bot_token.get_secret_value())
        connect_task = asyncio.create_task(bot.connect())

        try:
            yield {
                "agent": agent,
            }
        finally:
            await bot.close()
            await connect_task

    return initialize_app


class ApplicationStateStorage(t.Protocol):
    @property
    def state(self) -> State: ...


def get_agent(storage: ApplicationStateStorage, config: AgentServerConfig) -> WrappedResponseAgent:
    """Get the agent from the application state."""
    agent = storage.state.agent
    assert agent is not None, "Agent not initialized"
    return t.cast(WrappedResponseAgent, agent)


def app_factory(
    lifespan_factory: AppLifespanFactory[AgentServerConfig], config: AgentServerConfig
):
    logger.debug(f"loading application with config: {config}")
    app = setup_app(config, lifespan=lifespan_factory(config))
    return app

def extract_wrapped_response(response: WrappedResponse) -> str:
    match response.response:
        case StrResponse(blob=blob):
            return blob
        case SemanticResponse(query=query):
            return str(query)
        case SqlResponse(query=query):
            return query.query
        case ErrorResponse(message=message):
            return message
        case AnyResponse(raw=raw):
            return str(raw)
        case _:
            raise ValueError(f"Unsupported response type: {type(response.response)}")

def setup_app(config: AgentServerConfig, lifespan: t.Callable[[FastAPI], t.Any]):
    # Dependency to get the cluster manager

    setup_logging(3)

    app = FastAPI(lifespan=lifespan)

    @app.get("/status")
    async def get_status():
        """Liveness endpoint"""
        return {"status": "Service is running"}

    @app.post("/v0/chat")
    async def chat(
        request: Request,
        chat_request: ChatRequest,
    ):
        """Get the status of a job"""
        agent = get_agent(request, config)
        response = await agent.run_safe(
            chat_request.current_message.content,
            chat_history=chat_request.to_llama_index_chat_history(),
        )
        response_str = extract_wrapped_response(response)

        lines: list[str] = []
        message_id = str(uuid.uuid4())
        lines.append(f'f:{{"messageId":"{message_id}"}}\n')

        for line in response_str.split("\n"):
            escaped_line = json.dumps(line)
            lines.append(f"0:{escaped_line}\n")

        lines.append(
            'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
        )

        return PlainTextResponse("".join(lines))

    return app
