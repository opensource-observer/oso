import logging
import typing as t
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.datastructures import State
from fastapi.responses import PlainTextResponse
from oso_agent.agent.agent import Agent
from oso_agent.server.definition import (
    AgentServerConfig,
    AppLifespanFactory,
    ChatRequest,
)
from oso_agent.utils.log import setup_logging

load_dotenv()
logger = logging.getLogger(__name__)


def default_lifecycle(config: AgentServerConfig):
    @asynccontextmanager
    async def initialize_app(app: FastAPI):
        agent = await Agent.create(config)
        try:
            yield {
                "agent": agent,
            }
        finally:
            pass

    return initialize_app

class ApplicationStateStorage(t.Protocol):
    @property
    def state(self) -> State: ...

def get_agent(storage: ApplicationStateStorage, config: AgentServerConfig) -> Agent:
    """Get the agent from the application state."""
    agent = storage.state.agent
    assert agent is not None, "Agent not initialized"
    return t.cast(Agent, agent)

def app_factory(lifespan_factory: AppLifespanFactory[AgentServerConfig], config: AgentServerConfig):
    logger.debug(f"loading application with config: {config}")
    app = setup_app(config, lifespan=lifespan_factory(config))
    return app

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
        response = await agent.run(
            query=chat_request.current_message.content,
            chat_history=chat_request.to_llama_index_chat_history(),
        )

        # We should likely be streaming this, but for now, we'll just return the
        # whole response
        lines: list[str] = []
        lines.append(f'f:{{"messageId": "{str(uuid.uuid4())}"}}')
        for line in response.split("\n"):
            lines.append(f"0: {line}")
        lines.append('d:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n')

        return PlainTextResponse("\n".join(lines))

    return app
