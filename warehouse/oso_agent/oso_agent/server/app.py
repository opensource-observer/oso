import asyncio
import json
import logging
import typing as t
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.datastructures import State
from fastapi.responses import JSONResponse, PlainTextResponse
from oso_agent.agent import setup_default_agent_registry
from oso_agent.agent.agent_registry import AgentRegistry
from oso_agent.server.bot import setup_bot
from oso_agent.server.definition import (
    AgentServerConfig,
    AppLifespanFactory,
    BotConfig,
    ChatRequest,
)
from oso_agent.types.response import AnyResponse
from oso_agent.util.log import setup_logging
from oso_agent.workflows.default import setup_default_workflow_registry
from oso_agent.workflows.registry import WorkflowRegistry

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
from ..workflows.default import default_resolver_factory

setup_nest_asyncio()

load_dotenv()
logger = logging.getLogger(__name__)


def default_lifecycle(config: AgentServerConfig):
    @asynccontextmanager
    async def initialize_app(app: FastAPI):
        setup_telemetry(config)

        agent_registry = await setup_default_agent_registry(config)
        workflow_registry = await setup_default_workflow_registry(
            config, default_resolver_factory
        )

        bot_config = BotConfig()
        bot = await setup_bot(bot_config, agent_registry)
        await bot.login(bot_config.discord_bot_token.get_secret_value())
        connect_task = asyncio.create_task(bot.connect())

        try:
            yield {
                "workflow_registry": workflow_registry,
                "agent_registry": agent_registry,
            }
        finally:
            await bot.close()
            await connect_task

    return initialize_app


class ApplicationStateStorage(t.Protocol):
    @property
    def state(self) -> State: ...


def get_agent_registry(storage: ApplicationStateStorage) -> AgentRegistry:
    """Get the agent registry from the application state."""
    agent_registry = storage.state.agent_registry
    assert agent_registry is not None, "Agent registry not initialized"
    return t.cast(AgentRegistry, agent_registry)


def get_workflow_registry(storage: ApplicationStateStorage) -> WorkflowRegistry:
    """Get the workflow registry from the application state."""
    workflow_registry = storage.state.workflow_registry
    assert workflow_registry is not None, "Workflow registry not initialized"
    return t.cast(WorkflowRegistry, workflow_registry)


async def get_agent(
    storage: ApplicationStateStorage, config: AgentServerConfig
) -> WrappedResponseAgent:
    """Get the agent from the application state."""
    agent_registry = get_agent_registry(storage)
    agent = await agent_registry.get_agent(config.agent_name)
    return agent


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

    @app.post("/v0/text2sql")
    async def text2sql(
        request: Request,
        chat_request: ChatRequest,
    ) -> JSONResponse:
        """Get the status of a job"""
        workflow_registry = get_workflow_registry(request)

        iterative_workflow = await workflow_registry.get_workflow("iterative_text2sql")

        result = await iterative_workflow.wrapped_run(
            input=chat_request.current_message.content,
            synthesize_response=False,
            execute_sql=False,
        )

        sql_output = str(result.response)

        return JSONResponse({"sql": sql_output})

    @app.post("/v0/chat")
    async def chat(
        request: Request,
        chat_request: ChatRequest,
    ):
        """Get the status of a job"""
        agent = await get_agent(request, config)
        response = await agent.run_safe(
            chat_request.current_message.content,
            chat_history=chat_request.to_llama_index_chat_history(),
        )
        response_str = extract_wrapped_response(response)

        lines: list[str] = []
        message_id = str(uuid.uuid4())
        lines.append(f'f:{{"messageId":"{message_id}"}}\n')

        # Split the response into substrings of N characters and escape
        # newlines for json
        for i in range(0, len(response_str), config.chat_line_length):
            substring = response_str[i : i + config.chat_line_length]
            escaped_substring = json.dumps(substring)
            lines.append(f"0:{escaped_substring}\n")

        lines.append(
            'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
        )

        return PlainTextResponse("".join(lines))

    return app
