import logging
import time
from contextlib import asynccontextmanager

from aioprometheus.collectors import Summary

from .common import MetricsLabeler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def async_time(summary: Summary, base_labels: dict | None = None):
    """
    An asynchronous context manager to time a code block.
    """
    start_time = time.perf_counter()
    context = MetricsLabeler()
    if base_labels:
        context.set_labels(base_labels)
    try:
        yield context
    finally:
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        summary.observe(
            context.get_labels(), elapsed_time * 1000
        )  # Convert to milliseconds
