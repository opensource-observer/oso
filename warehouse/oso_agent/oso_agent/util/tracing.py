import logging
from typing import Optional

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.sdk import trace as trace_sdk
from phoenix.otel import register

from .config import AgentConfig

logger = logging.getLogger(__name__)

def setup_telemetry(config: AgentConfig) -> Optional[trace_sdk.TracerProvider]:
    """Setup OpenTelemetry tracing if enabled."""
    if not config.enable_telemetry:
        return None

    try:
        if not config.arize_phoenix_api_key.get_secret_value() and config.arize_phoenix_use_cloud:
            logger.warning(
                "Arize Phoenix API key is empty but cloud mode is enabled"
            )
            return None
        
        logger.info(f"Setting up telemetry with Arize Phoenix at {config.arize_phoenix_base_url}")

        tracer_provider = register(
            project_name=config.arize_phoenix_project_name,
            endpoint=config.arize_phoenix_traces_url,
            batch=True,
            headers={
                "api_key": config.arize_phoenix_api_key.get_secret_value(),
            },
            set_global_tracer_provider=True,
            verbose=False,
        )

        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info(f"Arize Phoenix telemetry initialized. Traces go to {config.arize_phoenix_traces_url}")
        return tracer_provider
    except Exception as e:
        logger.error(f"Failed to initialize telemetry: {e}")
        return None
