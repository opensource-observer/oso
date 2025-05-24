import logging
from typing import Optional

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from phoenix.otel import register

from .config import AgentConfig

logger = logging.getLogger(__name__)

def setup_telemetry(config: AgentConfig) -> Optional[trace_sdk.TracerProvider]:
    """Setup OpenTelemetry tracing if enabled."""
    if not config.enable_telemetry:
        return None

    try:
        if config.arize_phoenix_use_cloud:
            if not config.arize_phoenix_api_key.get_secret_value():
                logger.warning(
                    "Arize Phoenix API key is empty but cloud mode is enabled"
                )
                return None

            logger.info("Setting up telemetry with Arize Phoenix Cloud")

            tracer_provider = register(
                project_name="oso-agent",
                endpoint="https://app.phoenix.arize.com/v1/traces",
                batch=True,
                headers={
                    "api_key": config.arize_phoenix_api_key.get_secret_value(),
                },
                set_global_tracer_provider=False,
                verbose=False,
            )

            LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info("Phoenix Cloud telemetry successfully initialized")
            return tracer_provider

        logger.info(
            f"Setting up telemetry with local Phoenix at {config.arize_phoenix_traces_url}"
        )
        tracer_provider = trace_sdk.TracerProvider()
        phoenix_exporter = HTTPSpanExporter(endpoint=config.arize_phoenix_traces_url)
        phoenix_processor = SimpleSpanProcessor(phoenix_exporter)
        tracer_provider.add_span_processor(span_processor=phoenix_processor)

        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("Local telemetry successfully initialized")
        return tracer_provider

    except Exception as e:
        logger.error(f"Failed to initialize telemetry: {e}")
        return None
