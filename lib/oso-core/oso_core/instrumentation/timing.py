import logging
import time
from contextlib import asynccontextmanager

from aioprometheus.collectors import Summary

logger = logging.getLogger(__name__)


@asynccontextmanager
async def async_time(summary: Summary, labels: dict | None = None):
    """
    An asynchronous context manager to time a code block.
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        summary.observe(labels or {}, elapsed_time * 1000)  # Convert to milliseconds
