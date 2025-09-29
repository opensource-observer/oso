import asyncio
import json
import logging
import typing as t
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.datastructures import State
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
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
from oso_agent.types.streaming import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    OutputMessage,
    OutputTextContent,
    ResponseError,
    ResponsesRequest,
    ResponsesResponse,
    ThoughtsCollector,
    Usage,
    UsageDetails,
)
from oso_agent.util import WorkflowConfig
from oso_agent.util.log import setup_logging
from oso_agent.workflows.default import setup_default_workflow_registry
from oso_agent.workflows.registry import WorkflowRegistry
from oso_agent.workflows.text2sql.events import Text2SQLStartEvent
from oso_agent.workflows.text2sql.semantic import SemanticText2SQLWorkflow
from pydantic import SecretStr

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
from ..workflows.default import default_resolver_factory, workflow_resolver_factory

setup_nest_asyncio()

load_dotenv()
logger = logging.getLogger(__name__)


def default_lifecycle(config: AgentServerConfig):
    @asynccontextmanager
    async def initialize_app(app: FastAPI):
        setup_telemetry(config)

        agent_registry = await setup_default_agent_registry(config)
        workflow_registry = await setup_default_workflow_registry(
            config,
            await default_resolver_factory(config),
            workflow_resolver_factory,
        )

        bot = None
        connect_task = None

        if config.enable_discord_bot:
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
            if config.enable_discord_bot:
                if bot and connect_task:
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


def _create_chunk(
    completion_id: str,
    created_timestamp: int,
    model: str,
    delta: dict,
    finish_reason: str | None = None,
) -> str:
    """Create a streaming chunk in OpenAI format."""
    chunk = ChatCompletionChunk(
        id=completion_id,
        created=created_timestamp,
        model=model,
        choices=[{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    )
    return f"data: {chunk.model_dump_json()}\n\n"


async def _stream_thoughts(
    thoughts_collector: ThoughtsCollector,
    workflow_task: asyncio.Task,
    completion_id: str,
    created_timestamp: int,
    model: str,
) -> t.AsyncGenerator[str, None]:
    """Stream thoughts as they are generated."""
    last_thought_count = 0
    thoughts_task = asyncio.create_task(thoughts_collector.get_thoughts())

    while not workflow_task.done():
        try:
            current_thoughts = await asyncio.wait_for(thoughts_task, timeout=0.1)
            if len(current_thoughts) > last_thought_count:
                for thought in current_thoughts[last_thought_count:]:
                    thought_content = f" [{thought.category}] {thought.content}"
                    yield _create_chunk(
                        completion_id,
                        created_timestamp,
                        model,
                        {"content": thought_content + "\n"},
                    )

                last_thought_count = len(current_thoughts)

            thoughts_task = asyncio.create_task(thoughts_collector.get_thoughts())

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.warning(f"Error streaming thoughts: {e}")
            break

    try:
        final_thoughts = await thoughts_collector.get_thoughts()
        if len(final_thoughts) > last_thought_count:
            for thought in final_thoughts[last_thought_count:]:
                thought_content = f" [{thought.category}] {thought.content}"
                yield _create_chunk(
                    completion_id,
                    created_timestamp,
                    model,
                    {"content": thought_content + "\n"},
                )
    except Exception as e:
        logger.warning(f"Error streaming final thoughts: {e}")


async def stream_thoughts_and_response(
    thoughts_collector: ThoughtsCollector,
    workflow_task: asyncio.Task,
    completion_id: str,
    model: str,
    include_thoughts: bool = True,
) -> t.AsyncGenerator[str, None]:
    """Stream thoughts in real-time as they're generated, followed by the final response."""
    created_timestamp = int(datetime.now(timezone.utc).timestamp())

    yield _create_chunk(completion_id, created_timestamp, model, {"role": "assistant"})

    if include_thoughts:
        async for thought_chunk in _stream_thoughts(
            thoughts_collector, workflow_task, completion_id, created_timestamp, model
        ):
            yield thought_chunk

    try:
        workflow_result = await workflow_task
        final_response = extract_wrapped_response(workflow_result)
        yield _create_chunk(
            completion_id,
            created_timestamp,
            model,
            {"content": final_response},
        )

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        yield _create_chunk(
            completion_id,
            created_timestamp,
            model,
            {"content": f"\n\n**Error:** {str(e)}"},
        )

    yield _create_chunk(completion_id, created_timestamp, model, {}, "stop")
    yield "data: [DONE]\n\n"


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
        authorization: t.Annotated[str | None, Header()] = None,
    ) -> JSONResponse:
        """Get the status of a job"""
        oso_api_key = (
            authorization.removeprefix("Bearer ").strip()
            if authorization and authorization.startswith("Bearer ")
            else config.oso_api_key.get_secret_value()
        )
        workflow_config = WorkflowConfig(oso_api_key=SecretStr(oso_api_key))
        workflow_registry = get_workflow_registry(request)
        semantic_workflow = t.cast(
            SemanticText2SQLWorkflow,
            await workflow_registry.get_workflow("semantic_text2sql", workflow_config),
        )

        # NOTE: for now this workflow does not support chat history it only accepts the most recent message
        semantic_result = await semantic_workflow.wrapped_run(
            Text2SQLStartEvent(
                input=chat_request.current_message.content,
                synthesize_response=False,
                execute_sql=False,
            )
        )

        sql = str(semantic_result.response)

        return JSONResponse({"sql": sql})

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

    @app.post("/v0/chat/completions")
    async def chat_completions(
        request: Request,
        completion_request: ChatCompletionRequest,
    ):
        try:
            latest_message = completion_request.messages[-1]
            user_query = latest_message.get("content", "")

            completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"

            return await handle_streaming_completion(
                request,
                config,
                user_query,
                completion_id,
                completion_request.model,
                completion_request.thought,
            )

        except Exception as e:
            logger.error(f"Error in chat completions: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def _create_error_stream(
        completion_id: str, model: str, error_message: str
    ) -> t.AsyncGenerator[str, None]:
        """Create an error stream for failed completions."""
        error_chunk = ChatCompletionChunk(
            id=completion_id,
            created=int(datetime.now(timezone.utc).timestamp()),
            model=model,
            choices=[
                {
                    "index": 0,
                    "delta": {"content": f"Error: {error_message}"},
                    "finish_reason": "stop",
                }
            ],
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    async def handle_streaming_completion(
        request: Request,
        config: AgentServerConfig,
        user_query: str,
        completion_id: str,
        model: str,
        include_thoughts: bool = False,
    ) -> StreamingResponse:
        """Handle streaming chat completion with thoughts."""
        try:
            workflow_config = WorkflowConfig(oso_api_key=config.oso_api_key)
            workflow_registry = get_workflow_registry(request)

            # Models from marimo have a `oso/` prefix
            model = model.removeprefix("oso/")

            logger.debug(
                f"Starting streaming completion for {model} model...",
                extra={
                    "model": model,
                },
            )

            workflow = await workflow_registry.get_workflow(
                model,
                workflow_config,
            )

            workflow_task = asyncio.create_task(
                workflow.wrapped_run_from_kwargs(
                    input=user_query,
                    synthesize_response=True,
                    execute_sql=False,
                )
            )

            async def generate_stream():
                thoughts_collector = workflow.resolver.get_resource(
                    "thoughts_collector"
                )
                async for chunk in stream_thoughts_and_response(
                    thoughts_collector,
                    workflow_task,
                    completion_id,
                    model,
                    include_thoughts,
                ):
                    yield chunk

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            return StreamingResponse(
                _create_error_stream(completion_id, model, str(e)),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

    @app.post("/v0/responses")
    async def create_response(
        request: Request,
        responses_request: ResponsesRequest,
        authorization: t.Annotated[str | None, Header()] = None,
    ) -> JSONResponse:
        """Create a model response using OpenAI Responses API format."""
        try:
            oso_api_key = (
                authorization.removeprefix("Bearer ").strip()
                if authorization and authorization.startswith("Bearer ")
                else config.oso_api_key.get_secret_value()
            )

            response_id = f"resp_{uuid.uuid4().hex[:50]}"
            message_id = f"msg_{uuid.uuid4().hex[:50]}"
            created_at = int(datetime.now(timezone.utc).timestamp())

            if (
                isinstance(responses_request.input, list)
                or responses_request.input is None
            ):
                raise HTTPException(
                    status_code=400, detail="Only string input is currently supported"
                )

            user_input = responses_request.input

            workflow_config = WorkflowConfig(oso_api_key=SecretStr(oso_api_key))
            workflow_registry = get_workflow_registry(request)

            semantic_workflow = t.cast(
                SemanticText2SQLWorkflow,
                await workflow_registry.get_workflow(
                    "semantic_text2sql",
                    workflow_config,
                ),
            )

            semantic_result = await semantic_workflow.wrapped_run(
                Text2SQLStartEvent(
                    input=user_input,
                    synthesize_response=True,
                    execute_sql=False,
                )
            )

            response_text = extract_wrapped_response(semantic_result)

            output_content = OutputTextContent(
                type="output_text", text=response_text, annotations=[]
            )

            output_message = OutputMessage(
                id=message_id,
                type="message",
                status="completed",
                role="assistant",
                content=[output_content],
            )

            usage = Usage(
                input_tokens=len(user_input.split()) * 2,
                output_tokens=len(response_text.split()) * 2,
                total_tokens=len(user_input.split()) * 2
                + len(response_text.split()) * 2,
                input_tokens_details=UsageDetails(cached_tokens=0, reasoning_tokens=0),
                output_tokens_details=UsageDetails(reasoning_tokens=0),
            )

            response = ResponsesResponse(
                id=response_id,
                object="response",
                created_at=created_at,
                status="completed",
                model=responses_request.model,
                output=[output_message],
                error=None,
                incomplete_details=None,
                instructions=responses_request.instructions,
                max_output_tokens=responses_request.max_output_tokens,
                temperature=responses_request.temperature,
                top_p=responses_request.top_p,
                text=responses_request.text,
                reasoning=responses_request.reasoning,
                tools=responses_request.tools,
                tool_choice=responses_request.tool_choice,
                parallel_tool_calls=responses_request.parallel_tool_calls,
                previous_response_id=responses_request.previous_response_id,
                truncation=responses_request.truncation,
                max_tool_calls=responses_request.max_tool_calls,
                store=responses_request.store,
                usage=usage,
                metadata=responses_request.metadata,
                user=responses_request.user,
                safety_identifier=responses_request.safety_identifier,
                prompt_cache_key=responses_request.prompt_cache_key,
            )

            return JSONResponse(response.model_dump())

        except Exception as e:
            logger.error(f"Error in responses endpoint: {e}")
            error_response = ResponsesResponse(
                id=f"resp_{uuid.uuid4().hex[:50]}",
                object="response",
                created_at=int(datetime.now(timezone.utc).timestamp()),
                status="failed",
                model=responses_request.model,
                output=[],
                error=ResponseError(
                    type="api_error",
                    code="internal_error",
                    message=str(e),
                    param=None,
                ),
                incomplete_details=None,
                instructions=responses_request.instructions,
                max_output_tokens=responses_request.max_output_tokens,
                temperature=responses_request.temperature,
                top_p=responses_request.top_p,
                text=responses_request.text,
                reasoning=responses_request.reasoning,
                tools=responses_request.tools,
                tool_choice=responses_request.tool_choice,
                parallel_tool_calls=responses_request.parallel_tool_calls,
                previous_response_id=responses_request.previous_response_id,
                truncation=responses_request.truncation,
                max_tool_calls=responses_request.max_tool_calls,
                store=responses_request.store,
                usage=None,
                metadata=responses_request.metadata,
                user=responses_request.user,
                safety_identifier=responses_request.safety_identifier,
                prompt_cache_key=responses_request.prompt_cache_key,
            )

            return JSONResponse(error_response.model_dump(), status_code=500)

    return app
